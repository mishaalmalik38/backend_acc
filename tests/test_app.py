import pytest

def test_add():
    assert 1+1 == 2

def test_two():
    assert 10-2 == 8

@pytest.mark.parametrize("a, b, c",[(1,5,6),(2,2,4)])
def test_three(a,b,c):
    assert a+b == c

@pytest.fixture
def sample_data():
    return {"name":"mishaal","age":22}

def test_add_one_age(sample_data):
    cur=sample_data["age"] + 1
    assert cur == 23

def test_add_name(sample_data):
    full_name=sample_data["name"] + " malik"
    assert full_name == "mishaal malik"