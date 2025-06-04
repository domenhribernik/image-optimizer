from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from PIL import Image
import io
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

def optimize_image(request):
    """Main view for image optimization"""
    if request.method == 'GET':
        # Serve the upload form
        logger.info("Serving image optimizer form")
        return render(request, 'image_optimizer/upload.html')
    
    elif request.method == 'POST':
        logger.info(f"POST request received. Files: {list(request.FILES.keys())}")
        logger.info(f"POST data: {dict(request.POST)}")
        
        try:
            # Get uploaded file
            uploaded_file = request.FILES.get('image')
            if not uploaded_file:
                logger.error("No image file uploaded")
                return JsonResponse({'error': 'No image uploaded'}, status=400)
            
            logger.info(f"Processing file: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Get options from request
            max_size = int(request.POST.get('max_size', 1280))
            quality = int(request.POST.get('quality', 85))
            set_dpi = request.POST.get('set_dpi', 'true').lower() == 'true'
            strip_exif = request.POST.get('strip_exif', 'true').lower() == 'true'
            
            logger.info(f"Options - max_size: {max_size}, quality: {quality}, set_dpi: {set_dpi}, strip_exif: {strip_exif}")
            
            # Process the image
            optimized_image = process_image(
                uploaded_file, 
                max_size=max_size,
                quality=quality,
                set_dpi=set_dpi,
                strip_exif=strip_exif
            )
            
            if optimized_image:
                logger.info(f"Image processed successfully. Output size: {len(optimized_image)} bytes")
                # Create response with optimized image
                response = HttpResponse(optimized_image, content_type='image/jpeg')
                filename = os.path.splitext(uploaded_file.name)[0] + '_optimized.jpg'
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            else:
                logger.error("Failed to process image - unsupported format or processing error")
                return JsonResponse({'error': 'Unsupported image format or processing error'}, status=400)
                
        except ValueError as e:
            logger.error(f"ValueError in image processing: {str(e)}")
            return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in image processing: {str(e)}")
            return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)

def process_image(uploaded_file, max_size=1280, quality=85, set_dpi=True, strip_exif=True):
    """Process and optimize an uploaded image file"""
    try:
        logger.info(f"Opening image file: {uploaded_file.name}")
        
        # Open the image
        image = Image.open(uploaded_file)
        logger.info(f"Image opened successfully. Mode: {image.mode}, Size: {image.size}")
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if image.mode in ('RGBA', 'P', 'LA'):
            logger.info(f"Converting from {image.mode} to RGB")
            # Create white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            logger.info(f"Converting from {image.mode} to RGB")
            image = image.convert('RGB')
        
        original_size = image.size
        
        # Resize image while preserving aspect ratio
        if image.width > max_size or image.height > max_size:
            logger.info(f"Resizing image from {image.size} to max {max_size}px")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            logger.info(f"Resized to: {image.size}")
        else:
            logger.info(f"No resizing needed. Image size: {image.size}")
        
        # Prepare save options
        save_kwargs = {
            'format': 'JPEG',
            'quality': quality,
            'optimize': True
        }
        
        # Set DPI if requested
        if set_dpi:
            save_kwargs['dpi'] = (72, 72)
            logger.info("DPI set to 72")
        
        logger.info(f"Saving with options: {save_kwargs}")
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, **save_kwargs)
        output.seek(0)
        
        result = output.getvalue()
        logger.info(f"Image processing completed. Output size: {len(result)} bytes")
        return result
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None