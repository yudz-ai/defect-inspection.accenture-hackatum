# import subprocess
# bashCommand = "curl -L https://files.pythonhosted.org/packages/3a/5c/485e8724383b482cc6c739f3359991b8a93fb9316637af0ac954729545c9/googledrivedownloader-0.4-py2.py3-none-any.whl --output googledrivedownloader-0.4-py2.py3-none-any.whl"
# process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
# # output, error = process.communicate()
# bashCommand = "pip install ./googledrivedownloader-0.4-py2.py3-none-any.whl"
# process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
# output, error = process.communicate()

import logging
import os
import glob
import pyodbc
import requests
import azure.functions as func
from google_drive_downloader import GoogleDriveDownloader as gdd

class DagoAI:
    def __init__(self):
        self.data = []
        self.confidence_threshold = 0.75
        self.server = 'dago-ai-database.database.windows.net'
        self.database = 'customaidatabase'
        self.username = 'dagoai'
        self.password = '{AIDatabase1!}'   
        self.driver= '{ODBC Driver 17 for SQL Server}'

    def download_and_extract_images(self):
        if not os.path.exists('./images.zip'):
            gdd.download_file_from_google_drive(file_id="1fWlNIXSIY8rm-EsvsHcqq9PhlcznbFVr",
                                                dest_path='./images.zip',
                                                unzip=True) 
            os.remove('./images.zip')

    def detect_all_images(self):
        img_paths = glob.glob('./Images/*.png')
        for img_path in img_paths:
            with open(img_path, 'rb') as f:
                data = f.read()
            res = requests.post(url='https://customaiserver-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/fd1b5bfa-f004-44b3-92c8-37bc52fccd62/detect/iterations/Iteration1/image',
                                data=data,
                                headers={'Content-Type': 'application/octet-stream', 
                                        'Prediction-Key': '358951a4e32a4e06970ac572aa0c87ca'})
            # get filename
            filename = os.path.split(img_path)[-1]

            # get the best result
            res_json = res.json()
            probs = [pred['probability'] for pred in res_json['predictions']]
            probs_idx = max(range(len(probs)), key=probs.__getitem__)
            res_prediction = res_json['predictions'][probs_idx]

            # fetch the datas needed
            timestamp = res_json['created']#res_prediction['probability']
            probability = res_prediction['probability']
            result = 'Defect' if probability > self.confidence_threshold else 'NoDefect'
            bbox_left = res_prediction['boundingBox']['left']
            bbox_top = res_prediction['boundingBox']['top']
            bbox_width = res_prediction['boundingBox']['width']
            bbox_height = res_prediction['boundingBox']['height']
            print(filename, timestamp, result, probability, bbox_left, bbox_top, bbox_width, bbox_height)
            self.push_one_data(filename, timestamp, result, probability, bbox_left, bbox_top, bbox_width, bbox_height)

    def push_one_data(self, filename, timestamp, result, probability, bbox_left, bbox_top, bbox_width, bbox_height):
        with pyodbc.connect('DRIVER='+self.driver+';SERVER=tcp:'+self.server+';PORT=1433;DATABASE='+self.database+';UID='+self.username+';PWD='+ self.password) as conn:
            with conn.cursor() as cursor:
                # cursor.execute("SELECT * FROM [dbo].[DetectionData]")
                # cursor.execute("INSERT INTO [dbo].[DetectionData] ([TypeStr],[Result]) VALUES ('other2',1)")
                # print(f"INSERT INTO [dbo].[DetectionResult3] ([Filename],[Timestamp],[Result],[Probability],[BboxLeft],[BboxRight],[BboxWidth],[BboxHeight]) VALUES (aaa, bbb, ccc, {probability},  {bbox_left}, {bbox_top}, {bbox_width}, {bbox_height})")
                cursor.execute(f"INSERT INTO [dbo].[DetectionResult3] ([Filename],[Timestamp],[Result],[Probability],[BboxLeft],[BboxRight],[BboxWidth],[BboxHeight]) VALUES ('{filename}', '{timestamp}', '{result}', {probability},  {bbox_left}, {bbox_top}, {bbox_width}, {bbox_height})")
                conn.commit()

    def clean_database_first(self):
        with pyodbc.connect('DRIVER='+self.driver+';SERVER=tcp:'+self.server+';PORT=1433;DATABASE='+self.database+';UID='+self.username+';PWD='+ self.password) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM [dbo].[DetectionResult3]")
                conn.commit()
        
def main(req: func.HttpRequest) -> func.HttpResponse:
    dagoai = DagoAI()
    logging.info('Python HTTP trigger function processed a request.')

    # name = req.params.get('name')
    dagoai.download_and_extract_images()
    dagoai.clean_database_first()
    dagoai.detect_all_images()

    return func.HttpResponse(
        "This HTTP triggered function executed successfully. Now inferencing the model.",
        status_code=200
    )

    # if not name:
    #     try:
    #         req_body = req.get_json()
    #     except ValueError:
    #         pass
    #     else:
    #         name = req_body.get('name')

    # if name:
    #     return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    # else:
    #     return func.HttpResponse(
    #          "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
    #          status_code=200
    #     )
