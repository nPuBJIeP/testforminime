# import requests
def get_barcode(value):
    # 'http://barcodes4.me/barcode/{0}/{1}.{2}?IsTextDrawn=1'.format('c128b', value, 'png')
    # return 'http://barcodes4.me/barcode/{0}/{1}.{2}?IsTextDrawn=1'.format(
    #    'i2of5', value, 'png')

    # return 'https://bwipjs-api.metafloor.com/?bcid={0}&text={1}&includetext'.format('ean13', value)

    return 'https://barcode.tec-it.com/barcode.ashx?data={}&code=EAN13&multiplebarcodes=true&translate-esc=false&unit=Fit&dpi=96&imagetype=Png&rotation=0&color=%23000000&bgcolor=%23ffffff&qunit=Mm&quiet=0'.format(value)
