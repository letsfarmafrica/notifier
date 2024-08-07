from src import config
from pymongo import MongoClient
from urllib.parse import quote_plus
from pystac_client import Client
from odc.stac import load
from odc.algo import to_rgba
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from src.mailer.mailer import Mailer

from datetime import datetime, timedelta


mailer = Mailer()




class Reporter():

    def __init__(self):
        uri =  f"mongodb://{quote_plus(config.DB_ROOT)}:{quote_plus(config.DB_USERNAME)}@{config.DB_HOST}:{config.DB_PORT}/"
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[config.DB_NAME]
            self.collection = self.db[config.DB_COLLECTION]
        except Exception as e:
            raise(e)

    def lookup(self, user):
        api = Client.open("https://earth-search.aws.element84.com/v1")
        date = user['last_product_date']

        search = api.search(
        max_items = 15,
        limit = 5,
        collections = "sentinel-2-l2a",
        intersects = user["geometry"],
        datetime = f"{date}/{datetime.now().strftime('%Y-%m-%dT')}",
        )
        if search.matched() > 0 :
          return self.download_images(search, user)
        else:
            print("nothing to report")

    def download_images(self, item, user):
      geom = user["geometry"]
      data = load(item.items() ,geopolygon=geom, chunks={})
      ndvi = (data.nir - data.red) / (data.nir + data.red)
      rgba = to_rgba(data, bands=( "red", "green","blue" ),clamp=(1, 3000))
      swir = data.swir22

      for t in range(len(data.time)):
        _ndvi = ndvi.isel(time=t).compute()
        ndvi_image_data = BytesIO()
        plt.imsave(ndvi_image_data, _ndvi, format="png", cmap="RdYlGn", vmin=-1, vmax=1)
        ndvi_image_data.seek(0)

        _swir = swir.isel(time=t).compute().astype('float64')

        swir_image_data = BytesIO()
        plt.imsave(swir_image_data, _swir, format="png",cmap="magma", vmin=_swir.min(), vmax=_swir.max())
        swir_image_data.seek(0)

        _rgba = rgba.isel(time=t).compute()
        norm = plt.Normalize(vmin=_rgba.min(), vmax=_rgba.max())
        image = norm(_rgba)
        rgb_image_data = BytesIO()
        plt.imsave(rgb_image_data, image, format="png")
        rgb_image_data.seek(0)
        collection = item.item_collection_as_dict()
        stac = collection["features"][t]
        report_images = {
            "item": stac,
            "images":{
              "rgb": base64.b64encode(rgb_image_data.read()).decode('ascii'),
              "ndvi": base64.b64encode(ndvi_image_data.read()).decode('ascii'),
              "swir": base64.b64encode(swir_image_data.read()).decode('ascii')
            }
        }

        # send the email
        content = mailer.generate_template(report_images)
        mailer.send_email(content, user['email'])

        # update the db user's last downloaded item

        last_product_date = stac["properties"]["datetime"]
        new_last_date_object = datetime.strptime(last_product_date, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=1)
        new_last_date = new_last_date_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


        new_values = {
            "$set": {
                'last_product_date': new_last_date
            }
        }
        self.collection.update_one({'email': user['email']}, new_values)


      return len(data.time)

    def get_users(self):
            users = []
            items = self.collection.find()
            for item in items:
                users.append(item)
            return users

    def scan_and_download(self):
         users = self.collection.find()
         for user in users:
            return self.lookup(user)