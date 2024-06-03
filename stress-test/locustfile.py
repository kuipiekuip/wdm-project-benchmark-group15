import os.path
import random
import json

from locust import HttpUser, SequentialTaskSet, constant, task

from init_orders import NUMBER_OF_ORDERS


# Replace the example URLs and ports with the appropriate ones
with open("C:\\Users\\kuipe\\OneDrive\\Bureaublad\\TU Delft\\Master\\WDM\\wdm-project-benchmark\\urls.json") as f:
    urls = json.load(f)
    ORDER_URL = urls["ORDER_URL"]
    PAYMENT_URL = urls["PAYMENT_URL"]
    STOCK_URL = urls["STOCK_URL"]

class CreateAndCheckoutOrder(SequentialTaskSet):
    order_ids = []

    def on_start(self):
        # Fetch order IDs at the start of the test
        print(f"Fetching order IDs from {ORDER_URL}/orders/batch_find_orders/{NUMBER_OF_ORDERS}")
        response = self.client.get(f"{ORDER_URL}/orders/batch_find_orders/{NUMBER_OF_ORDERS}")
        if response.status_code == 200:
            self.order_ids = response.json().get("order_ids", [])
            # print(f"Fetched order IDs: {self.order_ids}")
        else:
            print(f"Failed to fetch order IDs, status code: {response.status_code}, response: {response.text}")

    @task
    def user_checks_out_order(self):
        if not self.order_ids:
            print("Order IDs not found, fetching again...")
            self.on_start()  # Ensure we have order IDs if not already fetched
        if self.order_ids:
            order_id = random.choice(self.order_ids)
            print(f"Checking out order ID: {order_id}")
            with self.client.post(f"{ORDER_URL}/orders/checkout/{order_id}", name="/orders/checkout/[order_id]", catch_response=True) as response:
                if 400 <= response.status_code < 500:
                    print(f"Checkout failed for order ID {order_id}, status code: {response.status_code}, response: {response.text}")
                    response.failure(response.text)
                else:
                    print(f"Checkout successful for order ID {order_id}")
                    response.success()
        else:
            print("No order IDs found, stopping the test.")
            

class MicroservicesUser(HttpUser):
    # How much time a user waits (seconds) to run another TaskSequence (you could also use between (start, end))
    wait_time = constant(1)
    # [SequentialTaskSet]: [weight of the SequentialTaskSet]
    tasks = {CreateAndCheckoutOrder: 100}
