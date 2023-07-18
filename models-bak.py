class Amendment(models.Model):
    product_name = models.CharField(max_length=50)
    brand_name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    organic = models.BooleanField()
    organic_certified = models.BooleanField()
    category = models.ForeignKey(AmendmentCategory, on_delete=models.CASCADE)
    type = models.ForeignKey(AmendmentType, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)

   @classmethod
    def create(cls, product_name, brand_name, country, organic, organic_certified, category, type, description):
        amendment = cls(product_name=product_name, brand_name=brand_name, country=country, organic=organic, 
                        organic_certified=organic_certified, category=category, type=type, description=description)
        amendment.save()
        return amendment

    @classmethod
    def retrieve(cls, id):
        return cls.objects.get(id=id)

    def update(self, **kwargs):
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)
        self.save()

    def delete_record(self):
        self.delete()

class AmendmentCategory(models.Model):
    category_name = models.CharField(max_length=50)

class AmendmentElement(models.Model):
    quantity = models.FloatField()
    units = models.CharField(max_length=20)
    amendment = models.ForeignKey(Amendment, on_delete=models.CASCADE)
    element = models.ForeignKey(Element, on_delete=models.CASCADE)

class AmendmentType(models.Model):
    type_name = models.CharField(max_length=50)

class Analysis(models.Model):
    analysis_date = models.DateField()
    description = models.CharField(max_length=255)
    soil_report = models.ForeignKey(SoilReport, on_delete=models.CASCADE)

class AnalysisItem(models.Model):
    description = models.CharField(max_length=255)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    report_item = models.ForeignKey(ReportItem, on_delete=models.CASCADE)

class Country(models.Model):
    country_name = models.CharField(max_length=50)

class Element(models.Model):
    element_name = models.CharField(max_length=50)
    common_name = models.CharField(max_length=50)
    element_symbol = models.CharField(max_length=20)
    description = models.CharField(max_length=255)

class Farm(models.Model):
    farm_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Field(models.Model):
    field_name = models.CharField(max_length=50)
    field_acres = models.FloatField()
    soil_type = models.CharField(max_length=50)
    growing_zone = models.IntegerField()
    description = models.CharField(max_length=255)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)

class SoilReport(models.Model):
    report_date = models.DateField()
    lab_name = models.CharField(max_length=50)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)

class ReportItem(models.Model):
    tested_element = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    results = models.FloatField()
    target_ratio = models.FloatField()
    target_level = models.FloatField()
    report = models.ForeignKey(SoilReport, on_delete=models.CASCADE)

class Source(models.Model):
    name = models.CharField(max_length=50)
    contact_name = models.CharField(max_length=50)
    street_address = models.CharField(max_length=50)
    town = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip = models.CharField(max_length=5)
    phone = models.CharField(max_length=10)
    email = models.EmailField(max_length=100)
    notes = models.CharField(max_length=255)

class SourceAmendment(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    amendment = models.ForeignKey(Amendment, on_delete=models.CASCADE)

class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    street_address = models.CharField(max_length=50)
    town = models.CharField(max_length=50)
    state = models.CharField(max_length=2)
    zip = models.CharField(max_length=5)
    phone = models.CharField(max_length=10)
    email = models.EmailField(max_length=100)
    notes = models.CharField(max_length=255)
    
    
class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    userId = models.IntegerField(default=0)
    user_stock_date = models.CharField(max_length=10, unique=True, null=True)
    date = models.DateField(default=None, null=True)
    open = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    high = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    low = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    close = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    volume = models.IntegerField(default=0, null=True)
    adj_high = models.DecimalField(max_digits=6, decimal_places=2,default=None, null=True)
    adj_low = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_close = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_open = models.DecimalField(max_digits=6, decimal_places=2, default=None,null=True)
    adj_volume = models.IntegerField(default=0, null=True)
    split_factor = models.DecimalField(max_digits=4, decimal_places=2, default=None,null=True)
    dividend = models.DecimalField(max_digits=5, decimal_places=2, default=None, null=True)
    symbol = models.CharField(max_length=10)
    exchange = models.CharField(max_length=6)

    def __str__(self):
        return f"{self.stock.id}: {self.close} ({self.date})"

    def save(self, request, *args, **kwargs):
        if not self.user_stock_date:
            current_user = request.user
            self.user_stock_date = f"{current_user}_{self.symbol}_{self.date.strftime('%Y-%m-%d')}"

        # Check for NaN values and replace them with None
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, float) and isnan(value):
                setattr(self, field.name, None)

         # Save the related stock object if it hasn't been saved yet
        if self.stock.pk is None:
            self.stock.save(request)

        existing_record = StockPrice.objects.filter(user_stock_date=self.user_stock_date).first()
        if not existing_record:
            with transaction.atomic():
                try:
                    super().save(request, *args, **kwargs)
                except IntegrityError:
                    existing = StockPrice.objects.get(stock_date=self.stock_date)
                    existing.date = self.date
                    existing.open = self.open
                    existing.high = self.high
                    existing.low = self.low
                    existing.close = self.close
                    existing.volume = self.volume
                    existing.adj_high = self.adj_high
                    existing.adj_low = self.adj_low
                    existing.adj_close = self.adj_close
                    existing.adj_open = self.adj_open
                    existing.adj_volume = self.adj_volume
                    existing.split_factor = self.split_factor
                    existing.dividend = self.dividend
                    existing.symbol = self.symbol
                    existing.exchange = self.exchange
                    existing.save()

class UserStock(models.Model):
    userId= models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.userId}: {self.stock.symbol}"

    @classmethod
    def add_user_stock(cls, request, symbol):
        current_user = request.user
        user_stock = cls(userId=current_user, symbol=symbol)
        user_stock.save()
        return user_stock

    @classmethod
    def get_user_stocks(cls, request):
        current_user = request.user
        user_stocks = cls.objects.filter(userId=current_user)
        return [user_stock.symbol for user_stock in user_stocks]
