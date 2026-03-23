def test_full_workflow(client):
    r = client.get("/health")
    assert r.status_code == 200

    # Create category
    r = client.post("/categories/", json={"name": "Coding", "description": "Dev prompts"})
    assert r.status_code == 201
    cat_id = r.json()["id"]

    # Create prompt with tags
    r = client.post("/prompts/", json={
        "title": "Python Docstring Generator",
        "template": "Write a docstring for:\n```python\n{{code}}\n```",
        "description": "Generates Google-style docstrings",
        "author": "alice",
        "model_hint": "gpt-4",
        "use_case": "coding",
        "category_ids": [cat_id],
        "tags": ["python", "documentation"],
    })
    assert r.status_code == 201
    prompt = r.json()
    prompt_id = prompt["id"]
    assert len(prompt["tags"]) == 2

    # Vote
    r = client.post(f"/prompts/{prompt_id}/vote", json={"value": 1})
    assert r.status_code == 200
    assert r.json()["upvotes"] == 1

    # Vote again = undo
    r = client.post(f"/prompts/{prompt_id}/vote", json={"value": 1})
    assert r.json()["upvotes"] == 0

    # Downvote
    r = client.post(f"/prompts/{prompt_id}/vote", json={"value": -1})
    assert r.json()["downvotes"] == 1

    # Feed: hot
    r = client.get("/prompts/", params={"feed": "hot"})
    assert r.json()["feed"] == "hot"

    # Fork
    r = client.post(f"/prompts/{prompt_id}/fork", json={"author": "bob"})
    assert r.status_code == 201
    assert r.json()["forked_from"] == prompt_id

    # Render
    r = client.post(f"/prompts/{prompt_id}/render", json={"values": {"code": "def add(a,b): return a+b"}})
    assert "def add" in r.json()["rendered"]

    # Tags endpoint
    r = client.get("/tags/")
    assert len(r.json()) == 2

    # Copy
    r = client.post(f"/prompts/{prompt_id}/copy")
    assert r.json()["copy_count"] == 1

    # Delete
    r = client.delete(f"/prompts/{prompt_id}")
    assert r.status_code == 204


def test_duplicate_category(client):
    client.post("/categories/", json={"name": "Writing"})
    r = client.post("/categories/", json={"name": "Writing"})
    assert r.status_code == 409