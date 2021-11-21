import os
import glob
import json
import base64
import pyodbc
import requests
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
            # os.remove('./images.zip')

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
            bbox_left = bbox_left + 0.5*bbox_width
            bbox_top = bbox_top + 0.5*bbox_height
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
        

def main():
    dagoai = DagoAI()

    dagoai.download_and_extract_images()
    dagoai.clean_database_first()
    dagoai.detect_all_images()

if __name__ == "__main__":
    main()