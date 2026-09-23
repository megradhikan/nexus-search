.PHONY: migrate ingest serve eval test index ui docker-up clean

migrate:
	python -m nexus.db.migrate

ingest:
	python -m nexus.ingest

serve:
	uvicorn nexus.api.main:app --reload --port 8000

eval:
	python -m nexus.eval

test:
	pytest tests/ -v

index:
	@echo "Run after bulk ingest:"
	@echo "CREATE INDEX idx_chunks_embedding_ivfflat ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"

ui:
	cd ui && npm run dev

docker-up:
	docker-compose up -d

clean:
	rm -f bm25_index.pkl
