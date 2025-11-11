# Yuvaa Ecommerce

A full-featured e-commerce platform built with Django, demonstrating modern web application development practices and comprehensive online shopping functionality.

## Overview

Yuvaa Ecommerce is a robust e-commerce solution that provides users with a seamless online shopping experience. The platform incorporates essential e-commerce features including user authentication, product management, shopping cart functionality, and secure payment processing.

## Key Features

### User Experience
- **User Management**: Complete authentication and registration system with profile management
- **Product Catalog**: Comprehensive product listings with detailed descriptions, high-quality images, and category filtering
- **Shopping Cart**: Intuitive cart management with real-time updates and quantity adjustments
- **Wishlist**: Save favorite items for future purchase
- **User Reviews & Ratings**: Customer feedback system with star ratings and detailed reviews
- **Search Functionality**: Advanced product search with filters and sorting options
- **Responsive Design**: Mobile-friendly interface for seamless shopping across all devices

### Payment Integration
- **Stripe Payment Gateway**: International credit/debit card processing with secure PCI compliance
- **M-Pesa Integration**: Mobile money payment system for Kenyan users
  - STK Push (Lipa Na M-Pesa Online) for seamless checkout
  - Real-time payment verification
  - Automatic order confirmation upon successful payment
  - Support for both Paybill and Till numbers

### Order Management
- **Order Tracking**: Real-time order status updates from placement to delivery
- **Purchase History**: Complete transaction history with invoice downloads
- **Order Notifications**: Email and SMS notifications for order updates
- **Delivery Management**: Multiple shipping options with tracking integration

### Administration
- **Admin Dashboard**: Comprehensive administrative panel for managing the entire platform
- **Product Management**: Add, edit, and remove products with bulk operations
- **Order Processing**: View and process orders with status management
- **User Management**: Monitor and manage user accounts and permissions
- **Analytics Dashboard**: Sales reports, revenue tracking, and customer insights
- **Inventory Management**: Stock level monitoring with low-stock alerts

## Technology Stack

### Backend
- **Language**: Python 3.x
- **Framework**: Django 4.x - High-level Python web framework
- **API**: Django REST Framework for RESTful API endpoints
- **Task Queue**: Celery for asynchronous task processing
- **Cache**: Redis for session management and caching

### Database
- **Development**: SQLite - Lightweight database for local development
- **Production**: PostgreSQL - Robust, scalable relational database
- **ORM**: Django ORM for database abstraction

### Frontend
- **Templates**: Django templating engine with Jinja2 syntax
- **Markup**: HTML5 with semantic structure
- **Styling**: CSS3, Bootstrap 5 for responsive design
- **Scripting**: JavaScript (ES6+), jQuery for interactive features
- **Icons**: Font Awesome for UI icons

### Payment Gateways
- **International Payments**: Stripe API
  - Credit/Debit card processing
  - Secure payment handling
  - Webhook integration for payment verification
- **Local Payments (Kenya)**: M-Pesa Daraja API
  - STK Push (Lipa Na M-Pesa Online)
  - C2B (Customer to Business) payments
  - Payment status queries
  - Callback URL handling

### Development Tools
- **Version Control**: Git, GitHub
- **Environment Management**: virtualenv/venv
- **Package Management**: pip, requirements.txt
- **API Testing**: Postman for endpoint testing

## Installation

### Prerequisites

- Python 3.8 or higher
- Django 4.x
- pip (Python package manager)
- PostgreSQL (for production deployment)
- Redis (for caching and Celery tasks)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/steve-ongera/Global-Mtumba.git
   cd Global-Mtumba
   ```

2. **Create and activate virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   
   Create a `.env` file in the project root and add the following variables:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   
   # Database Configuration
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # Stripe Configuration
   STRIPE_PUBLIC_KEY=your_stripe_public_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   
   # M-Pesa Configuration
   MPESA_CONSUMER_KEY=your_mpesa_consumer_key
   MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
   MPESA_SHORTCODE=your_business_shortcode
   MPESA_PASSKEY=your_lipa_na_mpesa_passkey
   MPESA_CALLBACK_URL=your_callback_url
   
   # Email Configuration (for notifications)
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_email_password
   ```

5. **Configure database settings**
   
   Update the database configuration in `settings.py` if needed. The project uses environment variables for secure configuration.

6. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser account**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

8. **Load initial data (optional)**
   ```bash
   python manage.py loaddata initial_data.json
   ```

9. **Collect static files (for production)**
   ```bash
   python manage.py collectstatic
   ```

10. **Start the development server**
    ```bash
    python manage.py runserver
    ```

11. **Access the application**
    
    - Main application: `http://127.0.0.1:8000`
    - Admin panel: `http://127.0.0.1:8000/admin`

## Project Demo

![Application Screenshot](screenshot_1.png)

## M-Pesa Integration Guide

### Overview
The platform integrates with Safaricom's M-Pesa Daraja API to enable mobile money payments for Kenyan customers. This provides a seamless checkout experience using the widely adopted M-Pesa payment system.

### Features
- **STK Push**: Automatic payment prompt sent to customer's phone
- **Real-time Verification**: Instant payment confirmation
- **Callback Handling**: Automated order processing upon successful payment
- **Transaction Tracking**: Complete payment history and reconciliation

### Setup Requirements
1. Register for M-Pesa Daraja API at [https://developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Create an app and obtain:
   - Consumer Key
   - Consumer Secret
   - Lipa Na M-Pesa Passkey
3. Configure your shortcode (Paybill or Till Number)
4. Set up callback URLs for payment notifications

### Implementation Details
The M-Pesa integration includes:
- Token generation and management
- STK Push initiation
- Payment status queries
- Callback URL handling for payment confirmation
- Error handling and retry mechanisms
- Transaction logging for audit trails

### Testing
Use Safaricom's sandbox environment for testing:
- Sandbox credentials provided by Safaricom
- Test phone numbers for simulating payments
- Comprehensive test cases for various scenarios

## API Documentation

### Payment Endpoints

#### Initiate M-Pesa Payment
```http
POST /api/payments/mpesa/initiate/
Content-Type: application/json

{
  "phone_number": "254712345678",
  "amount": 1000,
  "order_id": "ORD-12345"
}
```

#### Check Payment Status
```http
GET /api/payments/mpesa/status/{transaction_id}/
```

#### Stripe Payment
```http
POST /api/payments/stripe/checkout/
Content-Type: application/json

{
  "amount": 5000,
  "currency": "usd",
  "order_id": "ORD-12345"
}
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Configure allowed hosts in settings
- [ ] Use PostgreSQL database
- [ ] Set up proper CORS policies
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up Redis for caching
- [ ] Configure Celery for background tasks
- [ ] Set up automated backups
- [ ] Configure monitoring and logging
- [ ] Test all payment integrations
- [ ] Set up email notifications
- [ ] Configure static and media file serving

### Deployment Platforms
- **Heroku**: Easy deployment with Heroku CLI
- **AWS**: EC2, RDS, S3 for scalable infrastructure
- **DigitalOcean**: Droplets with managed databases
- **Railway**: Simple deployment with GitHub integration

## Project Structure

```
Global-Mtumba/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── apps/
│   ├── accounts/          # User authentication and profiles
│   ├── products/          # Product catalog and management
│   ├── cart/              # Shopping cart functionality
│   ├── orders/            # Order processing and tracking
│   ├── payments/          # Payment gateway integrations
│   │   ├── stripe/        # Stripe integration
│   │   └── mpesa/         # M-Pesa integration
│   └── reviews/           # Product reviews and ratings
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploaded files
├── templates/             # HTML templates
└── config/                # Project configuration
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add: your feature description"
   ```
4. **Push to your branch**
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request**

### Code Standards
- Follow PEP 8 style guide for Python code
- Write meaningful commit messages
- Include docstrings for functions and classes
- Add unit tests for new features
- Update documentation as needed

## Testing

Run the test suite:
```bash
python manage.py test
```

Run tests with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
```

## Security

- All sensitive data is stored in environment variables
- Passwords are hashed using Django's built-in authentication
- CSRF protection enabled for all forms
- XSS protection through Django templates
- SQL injection prevention via Django ORM
- Secure payment processing through PCI-compliant gateways
- Regular security updates and dependency patches

## Troubleshooting

### Common Issues

**M-Pesa Integration Issues**
- Verify your API credentials are correct
- Ensure callback URLs are publicly accessible
- Check that phone numbers are in correct format (254XXXXXXXXX)
- Confirm your shortcode is active

**Database Connection Errors**
- Verify PostgreSQL is running
- Check database credentials in .env file
- Ensure database exists and migrations are applied

**Static Files Not Loading**
- Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL settings
- Verify web server configuration

## Support & Documentation

- **Django Documentation**: [https://docs.djangoproject.com](https://docs.djangoproject.com)
- **Stripe API Docs**: [https://stripe.com/docs/api](https://stripe.com/docs/api)
- **M-Pesa Daraja API**: [https://developer.safaricom.co.ke/Documentation](https://developer.safaricom.co.ke/Documentation)

## Roadmap

### Upcoming Features
- [ ] Multi-currency support
- [ ] Advanced analytics dashboard
- [ ] AI-powered product recommendations
- [ ] Multi-vendor marketplace functionality
- [ ] Mobile application (iOS & Android)
- [ ] Social media integration
- [ ] Loyalty rewards program
- [ ] Live chat support
- [ ] Advanced inventory management
- [ ] International shipping integration

## Contact

**Steve Ongera**
- Email: steveongera001@gmail.com
- Phone: 0112284093

## License

This project is available for educational and commercial purposes.

---

*Built with Django - The web framework for perfectionists with deadlines*