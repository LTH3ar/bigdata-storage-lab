from kafka import KafkaConsumer
import json
import torch
from transformers import T5Tokenizer, T5EncoderModel
import torch.nn.functional as F
from dotenv import load_dotenv
import os

# Tải biến môi trường từ file .env
load_dotenv()

KAFKA_SERVER = "kafka:9092"
IMAGE_TOPIC = "image_topic"
CAPTION_TOPIC = "caption_topic"
TOP_RESULTS = 5

# Lấy query từ .env
QUERY = os.getenv("QUERY", "biển xanh")  # Mặc định là "biển xanh" nếu không có trong .env

# Tải mô hình và tokenizer T5
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5EncoderModel.from_pretrained("t5-small")
model.to(device)
model.eval()

def compute_embedding(text, tokenizer, model, device):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=64)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        encoder_outputs = model.encoder(**inputs)
    embeddings = encoder_outputs.last_hidden_state
    attention_mask = inputs["attention_mask"]
    mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    sum_embeddings = torch.sum(embeddings * mask_expanded, dim=1)
    sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    avg_embedding = sum_embeddings / sum_mask
    return avg_embedding.squeeze(0)

def process_stream():
    consumer_image = KafkaConsumer(
        IMAGE_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='earliest',
        group_id="t5-search-group"
    )

    consumer_caption = KafkaConsumer(
        CAPTION_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset='earliest',
        group_id="t5-search-group"
    )

    print("[t5-search] Đang chờ dữ liệu từ Kafka...")

    for message_image, message_caption in zip(consumer_image, consumer_caption):
        image_data = message_image.value
        caption_data = json.loads(message_caption.value)

        image_name = caption_data["image"]
        caption_text = caption_data["caption"]

        # Tính embedding cho caption
        caption_embedding = compute_embedding(caption_text, tokenizer, model, device)
        
        # Tính embedding cho query từ .env
        query_embedding = compute_embedding(QUERY, tokenizer, model, device)

        # Tính độ tương đồng với query
        similarity = F.cosine_similarity(query_embedding, caption_embedding, dim=0).item()

        print(f"Image: {image_name} - Caption: {caption_text} - Độ tương đồng: {similarity:.4f}")

if __name__ == "__main__":
    process_stream()


