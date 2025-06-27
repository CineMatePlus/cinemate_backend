from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(0.1, 0.2)  # kullanıcılar arasında kısa bekleme

    @task
    def get_data(self):
        self.client.get("/api/v1/movies?skip=0&limit=10")  # kendi endpoint'inle değiştir
