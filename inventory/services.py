import pandas as pd
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from django.db import models
from .models import ShopInventory


class InventoryPredictionService:
    """Service for inventory analytics and low stock predictions using Pandas"""
    
    @staticmethod
    def predict_stockout(inventory_id, days_ahead=30):
        """
        Predict when inventory will run out based on sales velocity
        
        Algorithm:
        1. Get last N days of sales data
        2. Calculate average daily sales
        3. Predict stockout date = current_stock / daily_sales_rate
        4. Apply seasonal adjustments if available
        """
        try:
            inventory = ShopInventory.objects.get(id=inventory_id)
            
            # Get sales data for the specified period
            start_date = timezone.now() - timedelta(days=days_ahead)
            sales_data = (
                inventory.transaction_items
                .filter(
                    transaction__created_at__gte=start_date,
                    transaction__status='COMPLETED'
                )
                .values('transaction__created_at')
                .annotate(quantity_sold=Sum('quantity'))
                .order_by('transaction__created_at')
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(list(sales_data))
            
            if df.empty:
                return {
                    'error': 'No sales data available for prediction',
                    'inventory_id': str(inventory_id)
                }
            
            # Calculate daily sales velocity
            df['date'] = pd.to_datetime(df['transaction__created_at']).dt.date
            daily_sales = df.groupby('date')['quantity_sold'].sum()
            avg_daily_sales = daily_sales.mean()
            
            # Predict stockout date
            if avg_daily_sales > 0:
                days_until_stockout = inventory.current_stock / avg_daily_sales
                predicted_stockout = timezone.now().date() + timedelta(days=days_until_stockout)
                
                # Update inventory with prediction
                inventory.predicted_stockout_date = predicted_stockout
                inventory.sales_velocity = avg_daily_sales
                inventory.save(update_fields=['predicted_stockout_date', 'sales_velocity'])
                
                return {
                    'inventory_id': str(inventory_id),
                    'medicine_name': inventory.master_medicine.brand_name,
                    'predicted_stockout_date': predicted_stockout.isoformat(),
                    'days_until_stockout': int(days_until_stockout),
                    'daily_sales_rate': round(avg_daily_sales, 2),
                    'current_stock': inventory.current_stock,
                    'reorder_level': inventory.reorder_level,
                    'needs_reorder': days_until_stockout < 30
                }
            else:
                return {
                    'inventory_id': str(inventory_id),
                    'medicine_name': inventory.master_medicine.brand_name,
                    'message': 'No sales velocity detected',
                    'current_stock': inventory.current_stock
                }
                
        except ShopInventory.DoesNotExist:
            return {
                'error': 'Inventory item not found',
                'inventory_id': str(inventory_id)
            }
        except Exception as e:
            return {
                'error': str(e),
                'inventory_id': str(inventory_id)
            }
    
    @staticmethod
    def batch_predict_stockouts(shop_id, days_ahead=30):
        """
        Run predictions for all inventory items in a shop
        """
        inventories = ShopInventory.objects.filter(
            shop__id=shop_id,
            is_active=True
        )
        
        results = []
        for inventory in inventories:
            result = InventoryPredictionService.predict_stockout(
                str(inventory.id),
                days_ahead
            )
            results.append(result)
        
        return results
    
    @staticmethod
    def get_expiring_soon(shop_id, days_threshold=30):
        """
        Get inventory items expiring within the threshold
        """
        threshold_date = timezone.now().date() + timedelta(days=days_threshold)
        
        expiring_items = ShopInventory.objects.filter(
            shop__id=shop_id,
            expiry_date__lte=threshold_date,
            expiry_date__gte=timezone.now().date(),
            is_active=True
        ).select_related('master_medicine')
        
        return [
            {
                'inventory_id': str(item.id),
                'medicine_name': item.master_medicine.brand_name,
                'generic_name': item.master_medicine.generic_name,
                'expiry_date': item.expiry_date.isoformat(),
                'expiry_status': item.expiry_status,
                'current_stock': item.current_stock,
                'batch_number': item.batch_number
            }
            for item in expiring_items
        ]
    
    @staticmethod
    def get_low_stock_alerts(shop_id):
        """
        Get inventory items with low stock based on threshold or prediction
        """
        low_stock_items = ShopInventory.objects.filter(
            shop__id=shop_id,
            is_active=True
        ).filter(
            models.Q(current_stock__lte=F('reorder_level')) |
            models.Q(predicted_stockout_date__lte=timezone.now().date() + timedelta(days=30))
        ).select_related('master_medicine')
        
        return [
            {
                'inventory_id': str(item.id),
                'medicine_name': item.master_medicine.brand_name,
                'current_stock': item.current_stock,
                'reorder_level': item.reorder_level,
                'predicted_stockout_date': item.predicted_stockout_date.isoformat() if item.predicted_stockout_date else None,
                'sales_velocity': item.sales_velocity,
                'urgency': 'HIGH' if item.current_stock == 0 else 'MEDIUM'
            }
            for item in low_stock_items
        ]
