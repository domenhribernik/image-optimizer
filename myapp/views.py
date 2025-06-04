from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from PIL import Image
import io
import os

def optimize_image(request):
    if request.method == 'GET':
        return render(request, 'image_optimizer/upload.html')
    
    elif request.method == 'POST':
        print(f"POST request received. Files: {list(request.FILES.keys())}")
        print(f"POST data: {dict(request.POST)}")
        
        try:
            uploaded_file = request.FILES.get('image')
            if not uploaded_file:
                print("ERROR: No image file uploaded")
                return JsonResponse({'error': 'No image uploaded'}, status=400)
            
            print(f"Processing file: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            max_size = int(request.POST.get('max_size', 1280))
            quality = int(request.POST.get('quality', 85))
            set_dpi = request.POST.get('set_dpi', 'true').lower() == 'true'
            strip_exif = request.POST.get('strip_exif', 'true').lower() == 'true'
            
            print(f"Options - max_size: {max_size}, quality: {quality}, set_dpi: {set_dpi}, strip_exif: {strip_exif}")
            
            optimized_image = process_image(
                uploaded_file, 
                max_size=max_size,
                quality=quality,
                set_dpi=set_dpi,
                strip_exif=strip_exif
            )
            
            if optimized_image:
                print(f"Image processed successfully. Output size: {len(optimized_image)} bytes")
                bytes_saved = uploaded_file.size - len(optimized_image)
                percent_saved = (bytes_saved / uploaded_file.size) * 100 if uploaded_file.size > 0 else 0
                print(f"{bytes_saved} bytes saved ({percent_saved:.2f}% reduction)")
                response = HttpResponse(optimized_image, content_type='image/jpeg')
                filename = os.path.splitext(uploaded_file.name)[0] + '_optimized.jpg'
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            else:
                print("ERROR: Failed to process image - unsupported format or processing error")
                return JsonResponse({'error': 'Unsupported image format or processing error'}, status=400)
                
        except ValueError as e:
            print(f"ERROR: ValueError in image processing: {str(e)}")
            return JsonResponse({'error': f'Invalid parameter: {str(e)}'}, status=400)
        except Exception as e:
            print(f"ERROR: Unexpected error in image processing: {str(e)}")
            return JsonResponse({'error': f'Processing error: {str(e)}'}, status=500)

def process_image(uploaded_file, max_size=1280, quality=85, set_dpi=True, strip_exif=True):
    try:
        print(f"Opening image file: {uploaded_file.name}")
        
        image = Image.open(uploaded_file)
        print(f"Image opened successfully. Mode: {image.mode}, Size: {image.size}")
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if image.mode in ('RGBA', 'P', 'LA'):
            print(f"Converting from {image.mode} to RGB")
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            print(f"Converting from {image.mode} to RGB")
            image = image.convert('RGB')
        
        original_size = image.size
        
        if image.width > max_size or image.height > max_size:
            print(f"Resizing image from {image.size} to max {max_size}px")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            print(f"Resized to: {image.size}")
        else:
            print(f"No resizing needed. Image size: {image.size}")
        
        save_kwargs = {
            'format': 'JPEG',
            'quality': quality,
            'optimize': True
        }
        
        if set_dpi:
            save_kwargs['dpi'] = (72, 72)
            print("DPI set to 72")
        
        print(f"Saving with options: {save_kwargs}")
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, **save_kwargs)
        output.seek(0)
        
        result = output.getvalue()
        print(f"Image processing completed. Output size: {len(result)} bytes")
        return result
        
    except Exception as e:
        print(f"ERROR: Error processing image: {str(e)}")
        return None