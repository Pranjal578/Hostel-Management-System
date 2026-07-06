"""
Pharmacy / Medical Store Blueprint
Handles: ShopOwner dashboard, inventory CRUD, orders, reviews, settings,
         and the public marketplace + medicine detail pages.
"""
import os
import uuid
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, current_app, abort)
from app.models.db import db, User, Shop, Medicine, MedicineOrder, MedicineReview
from app.routes.auth import role_required, log_security_action
from app.utils.email_sender import send_order_confirmation, send_order_status_update

pharmacy_bp = Blueprint('pharmacy', __name__)

# ─── Helpers ────────────────────────────────────────────────────────────────

def login_required(f):
    """Require any authenticated user (any role)"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def shop_owner_required(f):
    """Restrict to ShopOwner role only"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'ShopOwner':
            flash('Access denied. ShopOwner role required.', 'danger')
            return redirect(url_for('auth.dashboard_redirect'))
        return f(*args, **kwargs)
    return decorated


def get_current_shop():
    """Return the Shop object for the logged-in ShopOwner, or None"""
    return Shop.query.filter_by(owner_id=session['user_id']).first()


def save_medicine_photo(file, medicine_id):
    """
    Save a medicine photo to static/images/medicines/ with EXIF stripping.
    Returns the filename string, or None on failure.
    """
    try:
        from PIL import Image
        import io
        allowed = {'jpg', 'jpeg', 'png', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
        if ext not in allowed:
            return None
        img = Image.open(file)
        clean_io = io.BytesIO()
        fmt = 'JPEG' if ext in ('jpg', 'jpeg') else ext.upper()
        if fmt == 'WEBP':
            fmt = 'WEBP'
        img.save(clean_io, format=fmt)
        clean_io.seek(0)
        filename = f"med_{medicine_id}_{uuid.uuid4().hex[:8]}.{ext}"
        folder = os.path.join(current_app.root_path, 'static', 'images', 'medicines')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), 'wb') as out:
            out.write(clean_io.read())
        return filename
    except Exception as e:
        print(f"[WARN] Medicine photo save failed: {e}")
        return None


# ─── Public Marketplace Routes ───────────────────────────────────────────────

@pharmacy_bp.route('/marketplace')
def marketplace():
    """Public marketplace — list all approved shops with medicines"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    shops = Shop.query.filter_by(verification_status='Approved').all()

    # Collect all categories from all medicines for filter UI
    categories = set()
    for shop in shops:
        for med in shop.medicines:
            if med.category:
                categories.add(med.category.strip())

    return render_template('pharmacy/marketplace.html',
                           shops=shops,
                           query=query,
                           category=category,
                           categories=sorted(categories))


@pharmacy_bp.route('/shop/<int:shop_id>')
def shop_detail(shop_id):
    """Public shop page — list all available medicines in a shop"""
    shop = Shop.query.filter_by(id=shop_id, verification_status='Approved').first_or_404()
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('category', '').strip()

    medicines = Medicine.query.filter_by(shop_id=shop.id, is_available=True)
    if q:
        medicines = medicines.filter(
            db.or_(
                Medicine.name.ilike(f'%{q}%'),
                Medicine.salt_composition.ilike(f'%{q}%'),
                Medicine.category.ilike(f'%{q}%')
            )
        )
    if cat:
        medicines = medicines.filter_by(category=cat)
    medicines = medicines.all()

    categories = list({m.category for m in shop.medicines if m.category})
    return render_template('pharmacy/shop_detail.html',
                           shop=shop,
                           medicines=medicines,
                           categories=categories,
                           q=q,
                           cat=cat)


@pharmacy_bp.route('/medicine/<int:medicine_id>')
def medicine_detail(medicine_id):
    """Public medicine product page with reviews and Buy Now"""
    medicine = Medicine.query.get_or_404(medicine_id)
    if not medicine.is_available or medicine.shop.verification_status != 'Approved':
        abort(404)
    already_reviewed = False
    if 'user_id' in session:
        already_reviewed = MedicineReview.query.filter_by(
            medicine_id=medicine_id,
            reviewer_id=session['user_id']
        ).first() is not None
    return render_template('pharmacy/medicine_detail.html',
                           medicine=medicine,
                           shop=medicine.shop,
                           already_reviewed=already_reviewed)


@pharmacy_bp.route('/medicine/<int:medicine_id>/order', methods=['POST'])
@login_required
def place_order(medicine_id):
    """Submit a medicine order (any logged-in user)"""
    medicine = Medicine.query.get_or_404(medicine_id)
    if not medicine.is_available or medicine.shop.verification_status != 'Approved':
        flash('This medicine is currently unavailable.', 'danger')
        return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))

    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1
        delivery_option = request.form.get('delivery_option', 'Standard')
        payment_option = request.form.get('payment_option', 'UPI')
        delivery_address = request.form.get('delivery_address', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        notes = request.form.get('notes', '').strip()

        order = MedicineOrder(
            medicine_id=medicine.id,
            shop_id=medicine.shop_id,
            buyer_id=session['user_id'],
            quantity=quantity,
            total_price=round(medicine.price * quantity, 2),
            delivery_option=delivery_option,
            payment_option=payment_option,
            delivery_address=delivery_address,
            contact_phone=contact_phone,
            notes=notes,
            status='Pending'
        )
        db.session.add(order)
        db.session.flush()  # Get order.id before receipt upload

        # Handle receipt upload (UPI payment proof)
        receipt_file = request.files.get('receipt_file')
        if receipt_file and receipt_file.filename:
            filename = save_medicine_photo(receipt_file, f"receipt_{order.id}")
            if filename:
                order.receipt_path = filename

        db.session.commit()

        # Send confirmation email (best-effort)
        buyer = User.query.get(session['user_id'])
        try:
            send_order_confirmation(buyer.email, medicine.name, medicine.shop.shop_name, order.id)
        except Exception:
            pass

        log_security_action(session['user_id'], f"Placed order #{order.id} for medicine '{medicine.name}'")
        flash(f'Order placed successfully! Order #{order.id}. The shop will confirm soon.', 'success')
        return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to place order: {str(e)}', 'danger')
        return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))


@pharmacy_bp.route('/medicine/<int:medicine_id>/review', methods=['POST'])
@login_required
def submit_review(medicine_id):
    """Submit a star review + comment for a medicine"""
    medicine = Medicine.query.get_or_404(medicine_id)

    existing = MedicineReview.query.filter_by(
        medicine_id=medicine_id, reviewer_id=session['user_id']
    ).first()
    if existing:
        flash('You have already reviewed this medicine.', 'warning')
        return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))

    try:
        rating = int(request.form.get('rating', 0))
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars.', 'danger')
            return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))

        comment = request.form.get('comment', '').strip()
        review = MedicineReview(
            medicine_id=medicine_id,
            reviewer_id=session['user_id'],
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.flush()

        # Recalculate shop rating average
        medicine.shop.recalculate_rating()
        db.session.commit()

        flash('Thank you for your review!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to submit review: {str(e)}', 'danger')

    return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))


# ─── ShopOwner Dashboard & Inventory ─────────────────────────────────────────

@pharmacy_bp.route('/dashboard')
@shop_owner_required
def shop_dashboard():
    """ShopOwner main dashboard with inventory metrics and recent orders"""
    shop = get_current_shop()
    if not shop:
        flash('You do not have a registered shop yet.', 'info')
        return redirect(url_for('pharmacy.shop_settings'))

    # Stats
    total_medicines = Medicine.query.filter_by(shop_id=shop.id).count()
    available_medicines = Medicine.query.filter_by(shop_id=shop.id, is_available=True).count()
    low_stock = Medicine.query.filter(
        Medicine.shop_id == shop.id,
        Medicine.stock_quantity > 0,
        Medicine.stock_quantity <= 5
    ).all()
    out_of_stock = Medicine.query.filter_by(shop_id=shop.id, stock_quantity=0, is_available=True).count()
    recent_orders = MedicineOrder.query.filter_by(shop_id=shop.id).order_by(
        MedicineOrder.created_at.desc()
    ).limit(10).all()
    pending_orders = MedicineOrder.query.filter_by(shop_id=shop.id, status='Pending').count()
    total_revenue = db.session.query(
        db.func.sum(MedicineOrder.total_price)
    ).filter_by(shop_id=shop.id, status='Confirmed').scalar() or 0.0

    return render_template('pharmacy/shop_dashboard.html',
                           shop=shop,
                           total_medicines=total_medicines,
                           available_medicines=available_medicines,
                           low_stock=low_stock,
                           out_of_stock=out_of_stock,
                           recent_orders=recent_orders,
                           pending_orders=pending_orders,
                           total_revenue=total_revenue)


@pharmacy_bp.route('/inventory')
@shop_owner_required
def inventory():
    """ShopOwner inventory list"""
    shop = get_current_shop()
    if not shop:
        return redirect(url_for('pharmacy.shop_settings'))
    medicines = Medicine.query.filter_by(shop_id=shop.id).order_by(Medicine.created_at.desc()).all()
    return render_template('pharmacy/inventory.html', shop=shop, medicines=medicines)


@pharmacy_bp.route('/inventory/add', methods=['GET', 'POST'])
@shop_owner_required
def add_medicine():
    """Add a new medicine to inventory"""
    shop = get_current_shop()
    if not shop:
        flash('Please complete your shop registration first.', 'warning')
        return redirect(url_for('pharmacy.shop_settings'))
    if shop.verification_status != 'Approved':
        flash('Your shop must be approved by an admin before adding medicines.', 'warning')
        return redirect(url_for('pharmacy.shop_dashboard'))

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            price = float(request.form.get('price', 0))
            salt_composition = request.form.get('salt_composition', '').strip()
            category = request.form.get('category', '').strip()
            description = request.form.get('description', '').strip()
            stock_quantity = int(request.form.get('stock_quantity', 0))
            delivery_options = ','.join(request.form.getlist('delivery_options')) or 'Standard'
            payment_options = ','.join(request.form.getlist('payment_options')) or 'UPI,COD'
            is_available = request.form.get('is_available') == 'on'

            if not name or price <= 0:
                flash('Medicine name and a valid price are required.', 'danger')
                return render_template('pharmacy/add_medicine.html', shop=shop)

            medicine = Medicine(
                shop_id=shop.id,
                name=name,
                price=price,
                salt_composition=salt_composition,
                category=category,
                description=description,
                stock_quantity=stock_quantity,
                delivery_options=delivery_options,
                payment_options=payment_options,
                is_available=is_available
            )
            db.session.add(medicine)
            db.session.flush()

            # Handle photo upload
            photo = request.files.get('photo')
            if photo and photo.filename:
                filename = save_medicine_photo(photo, medicine.id)
                if filename:
                    medicine.photo_path = filename

            db.session.commit()
            log_security_action(session['user_id'], f"Added medicine '{name}' to shop #{shop.id}")
            flash(f'"{name}" added to inventory!', 'success')
            return redirect(url_for('pharmacy.inventory'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding medicine: {str(e)}', 'danger')

    return render_template('pharmacy/add_medicine.html', shop=shop)


@pharmacy_bp.route('/inventory/<int:medicine_id>/edit', methods=['GET', 'POST'])
@shop_owner_required
def edit_medicine(medicine_id):
    """Edit an existing medicine"""
    shop = get_current_shop()
    medicine = Medicine.query.get_or_404(medicine_id)
    if medicine.shop_id != shop.id:
        abort(403)

    if request.method == 'POST':
        try:
            medicine.name = request.form.get('name', medicine.name).strip()
            medicine.price = float(request.form.get('price', medicine.price))
            medicine.salt_composition = request.form.get('salt_composition', '').strip()
            medicine.category = request.form.get('category', '').strip()
            medicine.description = request.form.get('description', '').strip()
            medicine.stock_quantity = int(request.form.get('stock_quantity', 0))
            medicine.delivery_options = ','.join(request.form.getlist('delivery_options')) or 'Standard'
            medicine.payment_options = ','.join(request.form.getlist('payment_options')) or 'UPI,COD'
            medicine.is_available = request.form.get('is_available') == 'on'

            photo = request.files.get('photo')
            if photo and photo.filename:
                filename = save_medicine_photo(photo, medicine.id)
                if filename:
                    medicine.photo_path = filename

            db.session.commit()
            flash(f'"{medicine.name}" updated successfully.', 'success')
            return redirect(url_for('pharmacy.inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating medicine: {str(e)}', 'danger')

    return render_template('pharmacy/add_medicine.html', shop=shop, medicine=medicine, editing=True)


@pharmacy_bp.route('/inventory/<int:medicine_id>/delete', methods=['POST'])
@shop_owner_required
def delete_medicine(medicine_id):
    """Delete a medicine from inventory"""
    shop = get_current_shop()
    medicine = Medicine.query.get_or_404(medicine_id)
    if medicine.shop_id != shop.id:
        abort(403)
    name = medicine.name
    db.session.delete(medicine)
    db.session.commit()
    log_security_action(session['user_id'], f"Deleted medicine '{name}' from shop #{shop.id}")
    flash(f'"{name}" removed from inventory.', 'success')
    return redirect(url_for('pharmacy.inventory'))


# ─── Orders Management ───────────────────────────────────────────────────────

@pharmacy_bp.route('/orders')
@shop_owner_required
def orders():
    """ShopOwner order management"""
    shop = get_current_shop()
    if not shop:
        return redirect(url_for('pharmacy.shop_settings'))
    status_filter = request.args.get('status', '')
    q = MedicineOrder.query.filter_by(shop_id=shop.id)
    if status_filter:
        q = q.filter_by(status=status_filter)
    all_orders = q.order_by(MedicineOrder.created_at.desc()).all()
    return render_template('pharmacy/orders.html', shop=shop, orders=all_orders, status_filter=status_filter)


@pharmacy_bp.route('/orders/<int:order_id>/confirm', methods=['POST'])
@shop_owner_required
def confirm_order(order_id):
    """Confirm or reject a pending order"""
    shop = get_current_shop()
    order = MedicineOrder.query.get_or_404(order_id)
    if order.shop_id != shop.id:
        abort(403)
    action = request.form.get('action', 'confirm')
    if action == 'confirm':
        order.status = 'Confirmed'
        flash(f'Order #{order.id} confirmed.', 'success')
    else:
        order.rejection_reason = request.form.get('rejection_reason', '').strip()
        order.status = 'Rejected'
        flash(f'Order #{order.id} rejected.', 'warning')
    db.session.commit()

    # Notify buyer (best-effort)
    try:
        buyer = User.query.get(order.buyer_id)
        if buyer:
            send_order_status_update(buyer.email, order.status, order.medicine.name)
    except Exception:
        pass

    return redirect(url_for('pharmacy.orders'))


@pharmacy_bp.route('/orders/<int:order_id>/delivery-status', methods=['POST'])
@shop_owner_required
def update_delivery_status(order_id):
    """Update delivery stage of a confirmed order"""
    shop = get_current_shop()
    order = MedicineOrder.query.get_or_404(order_id)
    if order.shop_id != shop.id:
        abort(403)
    if order.status != 'Confirmed':
        flash('Cannot update delivery status of unconfirmed orders.', 'warning')
        return redirect(url_for('pharmacy.orders'))

    new_stage = request.form.get('delivery_status')
    if new_stage in MedicineOrder.DELIVERY_STAGES:
        order.delivery_status = new_stage
        db.session.commit()
        flash(f'Delivery status updated to: {new_stage}', 'success')
    else:
        flash('Invalid delivery stage.', 'danger')

    return redirect(url_for('pharmacy.orders'))


@pharmacy_bp.route('/my-orders')
@login_required
def my_orders():
    """View orders placed by the currently logged-in user with delivery status tracking"""
    user_orders = MedicineOrder.query.filter_by(buyer_id=session['user_id']).order_by(
        MedicineOrder.created_at.desc()
    ).all()
    return render_template('pharmacy/my_orders.html', orders=user_orders)


# ─── Reviews ─────────────────────────────────────────────────────────────────

@pharmacy_bp.route('/reviews')
@shop_owner_required
def reviews():
    """ShopOwner read-only review feed"""
    shop = get_current_shop()
    if not shop:
        return redirect(url_for('pharmacy.shop_settings'))
    all_reviews = []
    for med in shop.medicines:
        for review in med.reviews:
            all_reviews.append({'medicine': med, 'review': review})
    all_reviews.sort(key=lambda x: x['review'].created_at, reverse=True)
    return render_template('pharmacy/reviews.html', shop=shop, all_reviews=all_reviews)


# ─── Shop Settings ───────────────────────────────────────────────────────────

@pharmacy_bp.route('/settings', methods=['GET', 'POST'])
@shop_owner_required
def shop_settings():
    """Edit shop profile — license, contact, description"""
    shop = get_current_shop()

    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        license_number = request.form.get('license_number', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()

        if not shop_name or not license_number or not location:
            flash('Shop name, license number, and location are required.', 'danger')
            return render_template('pharmacy/shop_settings.html', shop=shop)

        if shop:
            shop.shop_name = shop_name
            shop.license_number = license_number
            shop.location = location
            shop.description = description
            shop.contact_phone = contact_phone
            shop.contact_email = contact_email
        else:
            shop = Shop(
                owner_id=session['user_id'],
                shop_name=shop_name,
                license_number=license_number,
                location=location,
                description=description,
                contact_phone=contact_phone,
                contact_email=contact_email,
                verification_status='Pending'
            )
            db.session.add(shop)

        db.session.commit()
        flash('Shop profile updated. Awaiting admin approval if newly registered.' if not shop.verification_status == 'Approved' else 'Shop profile updated.', 'success')
        return redirect(url_for('pharmacy.shop_dashboard'))

    return render_template('pharmacy/shop_settings.html', shop=shop)
