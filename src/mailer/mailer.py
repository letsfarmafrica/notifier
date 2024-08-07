

import os
import base64

from src import config

from mailjet_rest import Client

import pdfkit



class Mailer:

    def __init__(self):
        self.emailer = config.SERVICE_EMAIL
        self.mailjet = Client(auth=(config.API_KEY, config.API_SECRET), version="v3.1")

    def generate_template(self, images):
        item = images["item"]
        products_items = ''
        items_content = ''
        main_template = """
        <h1 style="color: #5e9ca0;">Weekly Report</h1>
        <h2 style="color: #2e6c80;">You have a products this week :)</h2>
        <p>There is an available product within the pre-specified area for you to download. <br />Below you have your report about this product.&nbsp;</p>
        <h2 style="color: #2e6c80;">Your product this week:</h2>
        """


        rgb_image_data = f'data:image/jpeg;base64,{images["images"]["rgb"]}'
        ndvi_image_data = f'data:image/jpeg;base64,{images["images"]["ndvi"]}'
        swir_image_data = f'data:image/jpeg;base64,{images["images"]["swir"]}'
        products_items += f'<li style="clear: both;">{item["id"]}</li>'
        items_content += f"""
        <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
        <h2 style="color: #2e6c80;">{item["id"]} :</h2>
        <table class="editorDemoTable" style="height: 162px;">
        <thead>
        <tr style="height: 18px;">
        <td style="height: 18px; width: 137.766px;">Identifier</td>
        <td style="height: 18px; width: 140.672px;">{item["id"]}</td>
        </tr>
        </thead>
        <tbody>
        <tr style="height: 18px;">
        <td style="height: 18px; width: 137.766px;">producttype</td>
        <td style="height: 18px; width: 140.672px;">{item["properties"]["s2:product_type"]}</td>
        </tr>
        </tr>
        <tr style="height: 18px;">
        <td style="width: 137.766px; height: 18px;">cloudcoverpercentage</td>
        <td style="width: 140.672px; height: 18px;">{item["properties"]["eo:cloud_cover"]}</td>
        </tr>
        </tbody>
        </table>
        <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;</p>
        <h2 style="color: #2e6c80;">True Colors Image :</h2>
        <p><img style="display: block; -webkit-user-select: none; margin: auto; background-color: hsl(0, 0%, 90%); transition: background-color 300ms;" src="{rgb_image_data}" /></p>
        </tr>
         <h2 style="color: #2e6c80;">NDVI:</h2>
        <p><img style="display: block; -webkit-user-select: none; margin: auto; background-color: hsl(0, 0%, 90%); transition: background-color 300ms;" src="{ndvi_image_data}" /></p>
        </tr>
         <h2 style="color: #2e6c80;">SWIR :</h2>
        <p><img style="display: block; -webkit-user-select: none; margin: auto; background-color: hsl(0, 0%, 90%); transition: background-color 300ms;" src="{swir_image_data}" /></p>
        """


        products_list = f'<ol style="list-style: none; font-size: 14px; line-height: 32px; font-weight: bold;">{products_items}</ol>'
        try:

            with open("temp_result.html", "w") as f:
                f.write(main_template + products_list + items_content)
            pdfkit.from_file('temp_result.html', 'output.pdf')

        except Exception as e:
            print(e)

        return main_template + products_list

    def send_email(self, content, email):


        try:
            with open('output.pdf', 'rb') as f:
                data = f.read()
            encoded_file = base64.b64encode(data).decode()

            data = {
            "Messages": [
                {
                "From": {
                    "Email": self.emailer,
                    "Name": "Me"
                },
                "To": [
                    {
                    "Email": email,
                    "Name": "You"
                    }
                ],
                "Subject": "Weekly report",
                "TextPart": "",
                "Attachments" : [
                    {
                        "ContentType" : "application/pdf",
                        "Filename" : "report.pdf",
                        "Base64Content" :  encoded_file
                    }
                ],
                "HTMLPart": content
                }
            ]
            }
            response = self.mailjet.send.create(data=data)

            os.remove('temp_result.html')
            os.remove('output.pdf')
            print(response.status_code)
            return response.status_code

        except Exception as e:
            print(e)