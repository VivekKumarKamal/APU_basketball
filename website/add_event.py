from flask import Blueprint, render_template, flash, redirect, url_for, request,abort
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
import os
from datetime import datetime
from .models import Event
from . import db


add_event = Blueprint('add_event', __name__)

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@add_event.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_new_event():
    # Check if the current user is authorized (admin with id=1)
    if current_user.id != 1:
        flash("You do not have permission to access this page.", category='error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        # Collect form data
        title = request.form.get('title')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        # button_url = request.form.get('button_url')
        image = request.files.get('image')  # File input for the image

        # Validate input
        if not title or not description or not image:
            flash('Please fill in all fields!', category='error')
        elif not allowed_file(image.filename):
            flash('Invalid image format! Allowed formats: png, jpg, jpeg.', category='error')
        else:
            # Convert string date to datetime object
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M') if start_date else None
                end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M') if end_date else None
            except ValueError:
                flash("Invalid date format. Please use the correct format.", category='error')
                return redirect(url_for('add_event.add_new_event'))

            # Save the image securely
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('website', 'static', 'assets', 'img', image_filename)

            # Make sure the directory exists
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            try:
                image.save(image_path)

                # Create and save a new Event
                new_event = Event(
                    title=title,
                    description=description,
                    img_url=image_filename,
                    start_date=start_date,
                    end_date=end_date,
                    admin_id=current_user.id  # Associate with the logged-in admin
                )
                db.session.add(new_event)
                db.session.commit()

                # Redirect to the home page with a success message
                flash('Event added successfully!', category='success')
                return redirect(url_for('views.home'))

            except Exception as e:
                # Handle unexpected errors
                flash(f"An error occurred: {str(e)}", category='error')

    return render_template("add_event.html")



@add_event.route('/event/<int:event_id>')
def event_page(event_id):
    # Fetch the event by ID
    event = Event.query.get(event_id)
    if not event or event.end_date <= datetime.now():
        # If event doesn't exist or has expired, return a 404 page
        abort(404)

    return render_template('event_page.html', event=event)

