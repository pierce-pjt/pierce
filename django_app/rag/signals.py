# rag/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, StockHolding

@receiver(post_save, sender=Transaction)
def update_stock_holding(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.user
    company = instance.company
    tx_type = instance.type
    price = instance.price
    quantity = instance.quantity

    # 보유 주식 가져오기 (없으면 생성)
    holding, _ = StockHolding.objects.get_or_create(
        user=user, 
        company=company,
        defaults={'quantity': 0, 'average_price': 0}
    )

    if tx_type == 'BUY':
        # 매수: 평단가 다시 계산 (이동평균법)
        # (기존총액 + 매수총액) / (기존수량 + 매수수량)
        total_quantity = holding.quantity + quantity
        if total_quantity > 0:
            current_total_value = holding.quantity * holding.average_price
            new_buy_value = quantity * price
            holding.average_price = (current_total_value + new_buy_value) / total_quantity
            holding.quantity = total_quantity
            
    elif tx_type == 'SELL':
        # 매도: 평단가는 그대로, 수량만 감소
        if holding.quantity >= quantity:
            holding.quantity -= quantity
        else:
            # (예외처리) 보유량보다 많이 팔 수 없음 -> 로직에 따라 에러 처리 가능
            print(f"⚠️ [Error] 보유 수량 부족: {holding.quantity} < {quantity}")
            return

    holding.save()
    print(f"✅ [Signal] 잔고 업데이트 완료: {company.name} | {holding.quantity}주 | 평단가 {holding.average_price}")