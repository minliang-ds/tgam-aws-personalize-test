from locust import HttpUser, TaskSet, task, between
import json
from random import randrange

PLATFORM = ['desktop', 'mobile']
CONTEXT = ['other', 'art_same_section_mostpopular']
SECTIONS = ['canada', 'investing', 'politics', 'opinion', 'sports']

class LoadTest(TaskSet):
    def on_start(self):
        self.id = f"90cc7426-8160-48f6-89ba-f41707d9ee{randrange(9)}{randrange(9)}"
        self.platform =  PLATFORM[randrange(2)]
        self.sections = SECTIONS[randrange(len(SECTIONS)+1)]

    @task
    def get_recommendations(self):

        with self.client.post("/v1/recommendations", json={
            "hash_id": self.id,
            "visitor_id": "90cc7426-8160-48f6-89ba-f41707d9ee1a",
            "platform": self.platform,
            "sub_requests": [
                {
                    "widget_id": "recommended-art_mostpopular",
                    "include_read": "false",
                    "include_content_types": "news,blog,column,review,gallery",
                    "last_content_ids": "KLRHQYKR3JFCRO4XYYEOVIAFSE",
                    "limit": 5,
                    "context": "art_mostpopular",
                    "min_content_age": 61,
                    "max_content_age": 86401,
                    "platform": "desktop",
                    "newsletter_ids": "",
                    "section": "/canada/",
                    "include_sections": self.sections,
                    "seo_keywords": "appwebview,cop26,climate change,climate crisis,environment,glasgow,yespop,yesapplenews",
                    "visitor_type": "anonymous"
                }
            ]
        }, headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0"
        }, catch_response=True) as response:

            try:
             parsed_response = json.loads(response.text)
             test = len(parsed_response[0]['recommendations'])
            except:
                test = 0

            if test == 0:
                response.failure("Got wrong response")


            print(f"Test: {self.id} {self.platform} {self.sections} {test}")
        #print("Response status code:", response.status_code)
        #print("Response content:", response.content)

    wait_time = between(0.5, 10)


class WebsiteUser(HttpUser):
    host = 'https://recoapi-prd.theglobeandmail.ca'
    tasks = [LoadTest]
    min_wait = 5000
    max_wait = 9000

