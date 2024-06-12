from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional



from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(
    prefix="/orders",
    tags=['Orders']
)


@router.get("/", response_model=List[schemas.Order])
def get_orders(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    posts = db.query(models.Order).filter(
        models.Order.pizza_size.contains(search)).limit(limit).offset(skip).all()
    return posts


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    new_order = models.Order(owner_id=current_user.id, **order.dict())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/{id}", response_model=schemas.Order)
def get_order(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Order).filter(models.Order.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")

    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    order_query = db.query(models.Order).filter(models.Order.id == id)

    order = order_query.first()

    if order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    if order.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    order_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=schemas.Order)
def update_order(id: int, updated_order: schemas.OrderCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    order_query = db.query(models.Order).filter(models.Order.id == id)

    order = order_query.first()

    if order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")

    if order.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    order_query.update(updated_order.dict(), synchronize_session=False)

    db.commit()

    return order_query.first()