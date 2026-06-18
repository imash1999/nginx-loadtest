from locust import HttpUser, task, between

class HeavyUser(HttpUser):
    wait_time = between(0.01, 0.05)  # очень агрессивно

    @task(5)
    def hit_heavy(self):
        self.client.get("/heavy")

    @task(1)
    def hit_root(self):
        self.client.get("/")
