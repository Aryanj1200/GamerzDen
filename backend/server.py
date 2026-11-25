from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Serve the actual GamerzDen pages from the frontend public folder.
PUBLIC_DIR = ROOT_DIR.parent / "frontend" / "public"

@app.get("/", include_in_schema=False)
async def manager_home():
    return FileResponse(PUBLIC_DIR / "GamerzDen_Manager_V8.html")

@app.get("/manager", include_in_schema=False)
@app.get("/GamerzDen_Manager_V8.html", include_in_schema=False)
async def manager_page():
    return FileResponse(PUBLIC_DIR / "GamerzDen_Manager_V8.html")

@app.get("/menu", include_in_schema=False)
@app.get("/menu.html", include_in_schema=False)
async def customer_menu_page():
    return FileResponse(PUBLIC_DIR / "menu.html")


# ---------- Models ----------
class Variant(BaseModel):
    name: str
    price: float
    partnerCost: Optional[float] = 0


class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    categoryId: Optional[str] = None
    partnerId: Optional[str] = None
    price: Optional[float] = None
    partnerCost: Optional[float] = 0
    variants: List[Variant] = []


class Category(BaseModel):
    id: str
    name: str


class Partner(BaseModel):
    id: str
    name: str
    sharePct: Optional[float] = 0  # legacy, kept for backwards compat


class MenuSync(BaseModel):
    items: List[MenuItem] = []
    categories: List[Category] = []
    partners: List[Partner] = []


class OrderItem(BaseModel):
    name: str
    variant: Optional[str] = ""
    price: float
    qty: int
    partnerId: Optional[str] = None
    partnerName: Optional[str] = ""
    partnerCost: Optional[float] = 0
    sharePct: Optional[float] = 0  # legacy


class OrderCreate(BaseModel):
    pc_id: str
    pc_name: str
    items: List[OrderItem]


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pc_id: str
    pc_name: str
    items: List[OrderItem]
    status: str = "pending"  # pending | preparing | delivered | rejected
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total: float = 0.0
    handled_by_manager: bool = False


class StatusUpdate(BaseModel):
    status: str
    handled_by_manager: Optional[bool] = None


# ---------- Health ----------
@api_router.get("/")
async def root():
    return {"status": "ok", "app": "GamerzDen Manager V8"}


# ---------- Menu ----------
@api_router.get("/menu")
async def get_menu():
    doc = await db.gd_menu.find_one({"_id": "current"}, {"_id": 0})
    if not doc:
        return {"items": [], "categories": [], "partners": []}
    doc.setdefault("items", [])
    doc.setdefault("categories", [])
    doc.setdefault("partners", [])
    return doc


@api_router.post("/menu")
async def set_menu(payload: MenuSync):
    doc = payload.model_dump()
    doc["_id"] = "current"
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.gd_menu.replace_one({"_id": "current"}, doc, upsert=True)
    return {"ok": True, "counts": {
        "items": len(payload.items),
        "categories": len(payload.categories),
        "partners": len(payload.partners),
    }}


# ---------- Orders ----------
@api_router.post("/orders", response_model=Order)
async def create_order(payload: OrderCreate):
    total = sum(i.price * i.qty for i in payload.items)
    order = Order(
        pc_id=payload.pc_id,
        pc_name=payload.pc_name,
        items=payload.items,
        total=total,
    )
    await db.gd_orders.insert_one(order.model_dump())
    return order


@api_router.get("/orders")
async def list_orders(status: Optional[str] = None, unhandled: Optional[bool] = None, limit: int = 50):
    q = {}
    if status:
        q["status"] = status
    if unhandled is True:
        q["handled_by_manager"] = False
    cursor = db.gd_orders.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(limit)


@api_router.get("/orders/{order_id}")
async def get_order(order_id: str):
    doc = await db.gd_orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Order not found")
    return doc


@api_router.put("/orders/{order_id}")
async def update_order(order_id: str, payload: StatusUpdate):
    update = {"status": payload.status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.handled_by_manager is not None:
        update["handled_by_manager"] = payload.handled_by_manager
    result = await db.gd_orders.update_one({"id": order_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Order not found")
    doc = await db.gd_orders.find_one({"id": order_id}, {"_id": 0})
    return doc


@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    await db.gd_orders.delete_one({"id": order_id})
    return {"ok": True}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
