import torch
print(torch.cuda.is_available())          # True bekleniyor
print(torch.cuda.get_device_name(0))      # Ekran kartı adı
