# Generated by Django 3.1.6 on 2021-02-18 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('persona', '0002_auto_20210205_1742'),
        ('general', '0003_auto_20210211_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bancos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=200)),
                ('estado', models.BooleanField()),
            ],
            options={
                'db_table': 'bancos',
            },
        ),
        migrations.CreateModel(
            name='CategoriasProductos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=100)),
                ('estado', models.BooleanField()),
            ],
            options={
                'db_table': 'categorias_productos',
            },
        ),
        migrations.CreateModel(
            name='FormaPago',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=50)),
                ('estado', models.BooleanField()),
            ],
            options={
                'db_table': 'forma_pago',
            },
        ),
        migrations.CreateModel(
            name='ModalidadPago',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=50)),
                ('estado', models.BooleanField()),
            ],
            options={
                'db_table': 'modalidad_pago',
            },
        ),
        migrations.CreateModel(
            name='OrdenCompra',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('folio_dte', models.CharField(max_length=50, null=True)),
                ('fecha_pago', models.DateTimeField(null=True)),
                ('monto_total', models.CharField(max_length=50, null=True)),
                ('total_descuento_beneficios', models.CharField(max_length=50, null=True)),
                ('ip', models.CharField(max_length=50, null=True)),
                ('id_sesion', models.CharField(max_length=50, null=True)),
                ('token_webpay', models.CharField(max_length=50, null=True)),
                ('pago_app', models.CharField(max_length=50, null=True)),
                ('comentario', models.CharField(max_length=50, null=True)),
                ('estado', models.BooleanField()),
                ('estado_pago', models.PositiveSmallIntegerField(choices=[(0, 'pendiente'), (1, 'pagada'), (2, 'rechazada'), (3, 'anulada'), (4, 'cancelada')])),
                ('forma_pago', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.formapago')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='persona.estudiante')),
            ],
            options={
                'db_table': 'orden_compra',
            },
        ),
        migrations.CreateModel(
            name='SubCategoriasProductos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=100)),
                ('estado', models.BooleanField()),
            ],
            options={
                'db_table': 'subcategorias_productos',
            },
        ),
        migrations.CreateModel(
            name='Productos',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=200)),
                ('codigo_interno', models.IntegerField(null=True)),
                ('descripcion_corta', models.CharField(max_length=200)),
                ('descripcion_larga', models.CharField(max_length=400)),
                ('unidad_medida', models.CharField(max_length=40, null=True)),
                ('stock', models.IntegerField()),
                ('valor', models.IntegerField()),
                ('valor_antes', models.IntegerField(null=True)),
                ('marca', models.CharField(max_length=200, null=True)),
                ('numero_serie', models.CharField(max_length=200, null=True)),
                ('destacado', models.BooleanField()),
                ('numero_vistas', models.IntegerField(null=True)),
                ('estado', models.BooleanField()),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.categoriasproductos')),
                ('subcategoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.subcategoriasproductos')),
            ],
            options={
                'db_table': 'productos',
            },
        ),
        migrations.CreateModel(
            name='PagoWebPay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('token', models.CharField(max_length=200)),
                ('response_code', models.CharField(max_length=200, null=True)),
                ('url_redirection', models.CharField(max_length=200, null=True)),
                ('buy_order', models.CharField(max_length=200, null=True)),
                ('session_id', models.CharField(max_length=200, null=True)),
                ('card_number', models.CharField(max_length=200, null=True)),
                ('card_expiration_date', models.CharField(max_length=200, null=True)),
                ('accounting_date', models.CharField(max_length=200, null=True)),
                ('transaction_date', models.CharField(max_length=200, null=True)),
                ('vci', models.CharField(max_length=200, null=True)),
                ('authorization_code', models.CharField(max_length=200, null=True)),
                ('payment_type', models.CharField(max_length=200, null=True)),
                ('amount', models.CharField(max_length=200, null=True)),
                ('shares_number', models.CharField(max_length=200, null=True)),
                ('commerce_code', models.CharField(max_length=200, null=True)),
                ('tbk_token', models.CharField(max_length=200, null=True)),
                ('tbk_orden_compra', models.CharField(max_length=200, null=True)),
                ('tbk_id_sesion', models.CharField(max_length=200, null=True)),
                ('resultado', models.CharField(max_length=200, null=True)),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_webpay',
            },
        ),
        migrations.CreateModel(
            name='PagoTransferenciaBancaria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre_titular_cuenta', models.CharField(max_length=200)),
                ('rut_titular_cuenta', models.CharField(max_length=20)),
                ('email_titular_cuenta', models.EmailField(max_length=200)),
                ('numero_operacion', models.CharField(max_length=50)),
                ('fecha_pago', models.DateTimeField()),
                ('valor', models.IntegerField()),
                ('mensaje', models.CharField(max_length=200, null=True)),
                ('estado', models.BooleanField()),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_transferencia_bancaria',
            },
        ),
        migrations.CreateModel(
            name='PagoRedCompra',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('credito_cuotas', models.IntegerField(null=True)),
                ('credito_sin_cuotas', models.IntegerField(null=True)),
                ('debito', models.IntegerField(null=True)),
                ('prepago', models.IntegerField(null=True)),
                ('valor', models.IntegerField()),
                ('numero_operacion', models.IntegerField()),
                ('fecha_pago', models.DateTimeField()),
                ('lectura_banda', models.IntegerField(null=True)),
                ('chip', models.IntegerField(null=True)),
                ('estado', models.BooleanField()),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_red_compra',
            },
        ),
        migrations.CreateModel(
            name='PagoEfectivo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('monto_pagado', models.IntegerField()),
                ('monto_vuelto', models.IntegerField()),
                ('monto_total', models.IntegerField()),
                ('estado', models.BooleanField()),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_efectivo',
            },
        ),
        migrations.CreateModel(
            name='PagoDepositoBancario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre_titular_cuenta', models.CharField(max_length=200)),
                ('rut_titular_cuenta', models.CharField(max_length=20)),
                ('numero_operacion', models.CharField(max_length=50)),
                ('fecha_pago', models.DateTimeField()),
                ('valor', models.IntegerField()),
                ('estado', models.BooleanField()),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_deposito_bancario',
            },
        ),
        migrations.CreateModel(
            name='PagoCheque',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('numero_cheque', models.IntegerField()),
                ('valor', models.IntegerField()),
                ('fecha_pago', models.DateTimeField()),
                ('nom_orden_de', models.IntegerField(null=True)),
                ('nom_no_orden_de', models.IntegerField(null=True)),
                ('estado', models.BooleanField()),
                ('tipo_cheque', models.PositiveSmallIntegerField(choices=[(0, 'al_portador'), (1, 'nominativo'), (2, 'cruzado'), (3, 'conformado'), (4, 'viajero')])),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.bancos')),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
            ],
            options={
                'db_table': 'pago_cheque',
            },
        ),
        migrations.CreateModel(
            name='OrdenCompraDetalle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=200)),
                ('valor', models.IntegerField()),
                ('cantidad', models.IntegerField()),
                ('descuento', models.IntegerField(null=True)),
                ('unidad_medida', models.IntegerField(null=True)),
                ('orden_compra', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.ordencompra')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.productos')),
            ],
            options={
                'db_table': 'orde_compra_detalle',
            },
        ),
        migrations.AddField(
            model_name='formapago',
            name='modalidad_pago',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pagos.modalidadpago'),
        ),
        migrations.CreateModel(
            name='DTE',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('folio', models.IntegerField()),
                ('codigo_tipo_dte_api', models.IntegerField()),
                ('ind_servicio', models.IntegerField(null=True)),
                ('fecha_emision', models.DateTimeField()),
                ('rut_emisor', models.CharField(max_length=50)),
                ('rut_receptor', models.CharField(max_length=50)),
                ('nombre_razon_social', models.CharField(max_length=200)),
                ('giro', models.CharField(max_length=200)),
                ('direccion', models.CharField(max_length=200)),
                ('ciudad', models.CharField(max_length=100, null=True)),
                ('path_file_pdf', models.CharField(max_length=200, null=True)),
                ('estado', models.BooleanField()),
                ('tipo_dte', models.PositiveSmallIntegerField(choices=[(0, 'boleta_iva'), (1, 'boleta_exenta'), (2, 'factura_iva'), (3, 'factura_exenta'), (4, 'nota_credito')])),
                ('comuna', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='general.comuna')),
            ],
            options={
                'db_table': 'dte',
            },
        ),
    ]
