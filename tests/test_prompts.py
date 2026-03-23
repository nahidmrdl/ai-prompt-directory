# tests/test_prompts.py
def test_full_workflow(client):
    # 1) Health check
    r = client.get("/health")
    assert r.status_code == 200

    # 2) Create category
    r = client.post("/categories/", json={"name": "Coding", "description": "Dev prompts"})
    assert r.status_code == 201
    cat_id = r.json()["id"]

    # 3) Create prompt
    prompt_data = {
        "title": "Python Docstring Generator",
        "template": "Write a docstring for:\n```python\n{{code}}\n```",
        "description": "Generates Google-style docstrings",
        "author": "alice",
        "model_hint": "gpt-4",
        "use_case": "coding",
        "category_ids": [cat_id],
    }
    r = client.post("/prompts/", json=prompt_data)
    assert r.status_code == 201
    prompt = r.json()
    prompt_id = prompt["id"]
    assert prompt["title"] == "Python Docstring Generator"
    assert "code" in prompt["variables"]
    assert len(prompt["categories"]) == 1

    # 4) List with search
    r = client.get("/prompts/", params={"search": "docstring"})
    assert r.json()["total"] >= 1

    # 5) Filter by category
    r = client.get("/prompts/", params={"category": cat_id})
    assert r.json()["total"] >= 1

    # 6) Render
    r = client.post(f"/prompts/{prompt_id}/render", json={"values": {"code": "def add(a,b): return a+b"}})
    assert r.status_code == 200
    assert "def add" in r.json()["rendered"]

    # 7) Rate
    r = client.post(f"/prompts/{prompt_id}/rate", params={"score": 4.5})
    assert r.status_code == 200
    assert r.json()["rating"] > 0

    # 8) Update
    r = client.patch(f"/prompts/{prompt_id}", json={"title": "Updated Title"})
    assert r.json()["title"] == "Updated Title"

    # 9) Delete
    r = client.delete(f"/prompts/{prompt_id}")
    assert r.status_code == 204


def test_duplicate_category(client):
    client.post("/categories/", json={"name": "Writing"})
    r = client.post("/categories/", json={"name": "Writing"})
    assert r.status_code == 409