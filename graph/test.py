from fastapi import FastAPI

app = FastAPI(title="Simple FastAPI Server")


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/items")
def get_items():
    return {"items": ["item1", "item2", "item3"]}


@app.post("/items")
def create_item(item: dict):
    return {"message": "Item created", "item": item}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: dict):
    return {"message": f"Item {item_id} updated", "item": item}


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}


@app.patch("/items/{item_id}")
def patch_item(item_id: int, item: dict):
    return {"message": f"Item {item_id} partially updated", "item": item}
