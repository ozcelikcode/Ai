"""
Resim optimizasyon utility'si
Resimleri kalitesini düşürmeden dosya boyutunu küçültür
"""

import os
import io
from PIL import Image, ImageOps
from pathlib import Path
from typing import Tuple, Optional, Union
import logging

logger = logging.getLogger(__name__)

# Varsayılan ayarlar
DEFAULT_MAX_WIDTH = 1920
DEFAULT_MAX_HEIGHT = 1080
DEFAULT_QUALITY = 85
DEFAULT_PROGRESSIVE = True

# Desteklenen formatlar
SUPPORTED_FORMATS = {
    'JPEG': {'extension': '.jpg', 'mode': 'RGB'},
    'PNG': {'extension': '.png', 'mode': 'RGBA'},
    'WEBP': {'extension': '.webp', 'mode': 'RGB'}
}

class ImageOptimizer:
    def __init__(self, 
                 max_width: int = DEFAULT_MAX_WIDTH,
                 max_height: int = DEFAULT_MAX_HEIGHT,
                 quality: int = DEFAULT_QUALITY,
                 progressive: bool = DEFAULT_PROGRESSIVE):
        """
        Resim optimizasyon sınıfı
        
        Args:
            max_width: Maksimum genişlik
            max_height: Maksimum yükseklik
            quality: JPEG kalitesi (1-100)
            progressive: Progressive JPEG kullan
        """
        self.max_width = max_width
        self.max_height = max_height
        self.quality = quality
        self.progressive = progressive
        
    def optimize_image(self, 
                      input_path: Union[str, Path, io.BytesIO], 
                      output_path: Optional[Union[str, Path]] = None,
                      target_format: str = 'JPEG') -> Tuple[bytes, str]:
        """
        Resmi optimize et
        
        Args:
            input_path: Girdi resim yolu veya BytesIO
            output_path: Çıktı yolu (opsiyonel)
            target_format: Hedef format (JPEG, PNG, WEBP)
            
        Returns:
            Tuple[bytes, str]: (optimize edilmiş resim bytes'ı, dosya uzantısı)
        """
        try:
            # Resmi aç
            if isinstance(input_path, io.BytesIO):
                image = Image.open(input_path)
            else:
                image = Image.open(input_path)
                
            # EXIF verilerini koru ve resmi düzelt
            image = ImageOps.exif_transpose(image)
            
            # Format ayarlarını al
            format_info = SUPPORTED_FORMATS.get(target_format.upper(), SUPPORTED_FORMATS['JPEG'])
            target_mode = format_info['mode']
            target_extension = format_info['extension']
            
            # Renk modunu dönüştür
            if image.mode != target_mode:
                if target_mode == 'RGB' and image.mode in ('RGBA', 'LA'):
                    # Şeffaf arka planı beyaza çevir
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image, mask=image.convert('RGBA').split()[-1])
                    image = background
                else:
                    image = image.convert(target_mode)
            
            # Boyutları kontrol et ve yeniden boyutlandır
            original_width, original_height = image.size
            new_width, new_height = self._calculate_new_dimensions(original_width, original_height)
            
            if (new_width, new_height) != (original_width, original_height):
                # Yüksek kaliteli resampling ile boyutlandır
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resim boyutu {original_width}x{original_height} -> {new_width}x{new_height}")
            
            # Optimize edilmiş resmi kaydet
            output_buffer = io.BytesIO()
            
            if target_format.upper() == 'JPEG':
                # JPEG için özel optimizasyonlar
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': self.quality,
                    'progressive': self.progressive,
                    'optimize': True
                }
            elif target_format.upper() == 'PNG':
                # PNG için özel optimizasyonlar
                save_kwargs = {
                    'format': 'PNG',
                    'optimize': True,
                    'compress_level': 6  # 0-9 arası, 6 optimal
                }
            elif target_format.upper() == 'WEBP':
                # WebP için özel optimizasyonlar
                save_kwargs = {
                    'format': 'WEBP',
                    'quality': self.quality,
                    'method': 6,  # 0-6 arası, 6 en iyi kalite
                    'lossless': False,
                    'optimize': True
                }
            else:
                save_kwargs = {'format': target_format.upper()}
            
            image.save(output_buffer, **save_kwargs)
            optimized_bytes = output_buffer.getvalue()
            output_buffer.close()
            
            # Eğer output_path belirtilmişse dosyaya kaydet
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(optimized_bytes)
                logger.info(f"Optimize edilmiş resim kaydedildi: {output_path}")
            
            # Dosya boyutu karşılaştırması
            original_size = len(input_path.getvalue()) if isinstance(input_path, io.BytesIO) else os.path.getsize(input_path)
            optimized_size = len(optimized_bytes)
            compression_ratio = ((original_size - optimized_size) / original_size) * 100
            
            logger.info(f"Dosya boyutu: {original_size} -> {optimized_size} bytes ({compression_ratio:.1f}% azalma)")
            
            return optimized_bytes, target_extension
            
        except Exception as e:
            logger.error(f"Resim optimizasyon hatası: {e}")
            raise
    
    def _calculate_new_dimensions(self, width: int, height: int) -> Tuple[int, int]:
        """
        Maksimum boyutlara göre yeni boyutları hesapla
        Aspect ratio'yu koruyarak
        """
        if width <= self.max_width and height <= self.max_height:
            return width, height
        
        # Aspect ratio'yu koru
        aspect_ratio = width / height
        
        if width > self.max_width:
            width = self.max_width
            height = int(width / aspect_ratio)
        
        if height > self.max_height:
            height = self.max_height
            width = int(height * aspect_ratio)
            
        return width, height
    
    @staticmethod
    def get_image_info(image_path: Union[str, Path, io.BytesIO]) -> dict:
        """
        Resim hakkında bilgi al
        """
        try:
            if isinstance(image_path, io.BytesIO):
                image = Image.open(image_path)
            else:
                image = Image.open(image_path)
                
            return {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'size': len(image_path.getvalue()) if isinstance(image_path, io.BytesIO) else os.path.getsize(image_path)
            }
        except Exception as e:
            logger.error(f"Resim bilgisi alınamadı: {e}")
            return {}
    
    @staticmethod
    def is_image(file_path: Union[str, Path]) -> bool:
        """
        Dosyanın resim olup olmadığını kontrol et
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False


# Global optimizer instance
default_optimizer = ImageOptimizer()

def optimize_uploaded_image(image_bytes: bytes, 
                          filename: str,
                          max_width: int = DEFAULT_MAX_WIDTH,
                          max_height: int = DEFAULT_MAX_HEIGHT,
                          quality: int = DEFAULT_QUALITY) -> Tuple[bytes, str]:
    """
    Yüklenmiş resmi optimize et
    
    Args:
        image_bytes: Resim byte verileri
        filename: Orijinal dosya adı
        max_width: Maksimum genişlik
        max_height: Maksimum yükseklik
        quality: Kalite (1-100)
        
    Returns:
        Tuple[bytes, str]: (optimize edilmiş bytes, yeni uzantı)
    """
    # Dosya uzantısından formatı belirle
    file_extension = Path(filename).suffix.lower()
    
    if file_extension in ['.jpg', '.jpeg']:
        target_format = 'JPEG'
    elif file_extension == '.png':
        target_format = 'PNG'
    elif file_extension == '.webp':
        target_format = 'WEBP'
    else:
        # Varsayılan olarak JPEG'e çevir
        target_format = 'JPEG'
    
    # Optimizer oluştur
    optimizer = ImageOptimizer(
        max_width=max_width,
        max_height=max_height,
        quality=quality
    )
    
    # Resmi optimize et
    input_buffer = io.BytesIO(image_bytes)
    optimized_bytes, extension = optimizer.optimize_image(input_buffer, target_format=target_format)
    
    return optimized_bytes, extension


# Farklı kullanım senaryoları için preset'ler
PRESETS = {
    'thumbnail': ImageOptimizer(max_width=300, max_height=300, quality=80),
    'medium': ImageOptimizer(max_width=800, max_height=600, quality=85),
    'large': ImageOptimizer(max_width=1920, max_height=1080, quality=90),
    'hero': ImageOptimizer(max_width=2560, max_height=1440, quality=92)
}

def optimize_with_preset(image_bytes: bytes, preset_name: str = 'medium') -> Tuple[bytes, str]:
    """Preset ile resmi optimize et"""
    optimizer = PRESETS.get(preset_name, PRESETS['medium'])
    input_buffer = io.BytesIO(image_bytes)
    return optimizer.optimize_image(input_buffer, target_format='JPEG')