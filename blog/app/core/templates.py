from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Türkçe yorum: Ortak Jinja2 templates nesnesi ve filtre kayıtları burada yönetilir.
from app.utils.helpers import strip_html_tags, get_excerpt


templates = Jinja2Templates(directory="templates")

# Jinja2 filter kayıtları
templates.env.filters['strip_html'] = strip_html_tags
templates.env.filters['excerpt'] = get_excerpt


# Site ayarlarını tüm şablon context'lerine eklemek için TemplateResponse override
_original_template_response = templates.TemplateResponse


def _template_response_with_settings(name: str, context: dict, status_code: int = 200, **kwargs) -> HTMLResponse:
    # Türkçe yorum: Tüm şablonlara site ayarlarını enjekte eder (varsa).
    if "site_settings" not in context and "request" in context:
        try:
            from app.core.database import SessionLocal
            from app.models.models import Settings
            db = SessionLocal()
            try:
                context["site_settings"] = db.query(Settings).first()
            finally:
                db.close()
        except Exception:
            context["site_settings"] = None

    return _original_template_response(name, context, status_code=status_code, **kwargs)


templates.TemplateResponse = _template_response_with_settings


