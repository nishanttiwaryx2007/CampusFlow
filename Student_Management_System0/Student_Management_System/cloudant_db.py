
import os

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from ibmcloudant.cloudant_v1 import CloudantV1


class CloudantStore:

    def __init__(self):

        url = os.getenv("CLOUDANT_URL", "").strip()
        key = os.getenv("CLOUDANT_APIKEY", "").strip()

        self.name = os.getenv(
            "CLOUDANT_DATABASE",
            "student_management"
        )

        if not url or not key:
            raise RuntimeError(
                "IBM Cloudant credentials are missing."
            )

        authenticator = IAMAuthenticator(key)

        self.client = CloudantV1(
            authenticator=authenticator
        )

        self.client.set_service_url(url)

        try:
            self.client.get_database_information(
                db=self.name
            ).get_result()

            print("Cloudant database connected successfully!")

        except ApiException as e:

            if e.status_code == 404:

                self.client.put_database(
                    db=self.name
                ).get_result()

                print("Cloudant database created successfully!")

            else:
                raise

    def find(self, selector):
        return self.client.post_find(
            db=self.name,
            selector=selector,
            limit=1000
        ).get_result().get("docs", [])

    def find_one(self, selector):
        rows = self.find(selector)
        return rows[0] if rows else None

    def count(self, selector):
        return len(self.find(selector))

    def get(self, doc_id):
        return self.client.get_document(
            db=self.name,
            doc_id=doc_id
        ).get_result()

    def insert(self, doc):
        return self.client.post_document(
            db=self.name,
            document=doc
        ).get_result()

    def update(self, doc):
        return self.client.post_document(
            db=self.name,
            document=doc
        ).get_result()

    def delete(self, doc):
        self.client.delete_document(
            db=self.name,
            doc_id=doc["_id"],
            rev=doc["_rev"]
        ).get_result()
