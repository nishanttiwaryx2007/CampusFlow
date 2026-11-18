import os
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibmcloudant.cloudant_v1 import CloudantV1

class CloudantStore:
    def __init__(self):
        url=os.getenv("CLOUDANT_URL","").strip()
        key=os.getenv("CLOUDANT_APIKEY","").strip()
        self.name=os.getenv("CLOUDANT_DATABASE","student_management")
        if not url or not key:
            raise RuntimeError("IBM Cloudant is not configured. Copy .env.example to .env and add CLOUDANT_URL and CLOUDANT_APIKEY.")
        self.client=CloudantV1(authenticator=IAMAuthenticator(key))
        self.client.set_service_url(url)
        try: self.client.get_database_information(db=self.name).get_result()
        except Exception: self.client.put_database(db=self.name).get_result()
    def find(self,selector):
        return self.client.post_find(db=self.name,selector=selector,limit=1000).get_result().get("docs",[])
    def find_one(self,selector):
        rows=self.find(selector); return rows[0] if rows else None
    def count(self,selector): return len(self.find(selector))
    def get(self,doc_id): return self.client.get_document(db=self.name,doc_id=doc_id).get_result()
    def insert(self,doc): return self.client.post_document(db=self.name,document=doc).get_result()
    def update(self,doc): return self.client.post_document(db=self.name,document=doc).get_result()
    def delete(self,doc): self.client.delete_document(db=self.name,doc_id=doc["_id"],rev=doc["_rev"]).get_result()
