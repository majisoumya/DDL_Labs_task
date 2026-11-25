"""API routers package for InsightIQ AI."""

from app.api.analyst import analyst_router
from app.api.charts import charts_router
from app.api.customers import router as customers_router
from app.api.dashboard import router as dashboard_router
from app.api.export import export_router
from app.api.health import router as health_router
from app.api.insights import insights_router
from app.api.products import router as products_router
from app.api.sales import router as sales_router
from app.api.system import system_router

__all__ = [
    "health_router",
    "dashboard_router",
    "sales_router",
    "products_router",
    "customers_router",
    "charts_router",
    "analyst_router",
    "export_router",
    "system_router",
    "insights_router",
]
