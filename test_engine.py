import pytest
from quantum_engine import (
    generate_binary,
    binary_to_hex,
    generate_password,
    generate_quantum_record,
    calculate_entropy_metrics,
    create_hadamard_circuit,
    QuantumRNG,
    UPPERCASE_CHARS,
    LOWERCASE_CHARS,
    DIGIT_CHARS,
    DEFAULT_SPECIAL_CHARS,
)


def test_generate_binary_length():
    """Test if generate_binary returns the correct length string of 0s and 1s."""
    binary_str = generate_binary(16, batch_size=4)
    assert len(binary_str) == 16
    assert all(c in ("0", "1") for c in binary_str)


def test_binary_to_hex():
    """Test binary to hexadecimal conversion logic."""
    assert binary_to_hex("1010") == "A"
    assert binary_to_hex("1010", uppercase=False) == "a"
    assert binary_to_hex("11110000") == "F0"
    # Testing padding logic
    assert binary_to_hex("1") == "1"


def test_generate_password_length():
    """Test if the final password matches the requested character length."""
    pwd_16 = generate_password(16)
    assert len(pwd_16) == 16

    pwd_32 = generate_password(32)
    assert len(pwd_32) == 32


def test_consecutive_passwords_differ():
    """Test that two consecutively generated passwords are not identical (quantum randomness)."""
    pwd1 = generate_password(32)
    pwd2 = generate_password(32)
    assert pwd1 != pwd2


def test_combined_upper_and_lower_case():
    """Test that generated password integrates BOTH uppercase and lowercase in the same output."""
    for _ in range(5):
        pwd = generate_password(16, use_uppercase=True, use_lowercase=True, use_digits=True, use_special=True)
        has_upper = any(c in UPPERCASE_CHARS for c in pwd)
        has_lower = any(c in LOWERCASE_CHARS for c in pwd)
        assert has_upper, f"Password {pwd} missing uppercase characters"
        assert has_lower, f"Password {pwd} missing lowercase characters"


def test_special_characters_integration():
    """Test that special characters are properly integrated into the generated password."""
    for _ in range(5):
        pwd = generate_password(16, use_uppercase=True, use_lowercase=True, use_digits=True, use_special=True)
        has_special = any(c in DEFAULT_SPECIAL_CHARS for c in pwd)
        assert has_special, f"Password {pwd} missing special characters"


def test_all_character_types_present():
    """Test that uppercase, lowercase, numbers, and special characters all coexist in output."""
    pwd = generate_password(24, ensure_each_type=True)
    assert any(c in UPPERCASE_CHARS for c in pwd), "Missing uppercase"
    assert any(c in LOWERCASE_CHARS for c in pwd), "Missing lowercase"
    assert any(c in DIGIT_CHARS for c in pwd), "Missing digits"
    assert any(c in DEFAULT_SPECIAL_CHARS for c in pwd), "Missing special characters"


def test_custom_special_characters():
    """Test that custom special character sets can be supplied."""
    custom_specials = "!#$"
    pwd = generate_password(
        16,
        use_uppercase=False,
        use_lowercase=False,
        use_digits=False,
        use_special=True,
        special_chars=custom_specials,
    )
    assert len(pwd) == 16
    assert all(c in custom_specials for c in pwd)


def test_quantum_record_structure():
    """Test that generate_quantum_record produces complete audit and entropy metadata."""
    record = generate_quantum_record(length=16)
    assert "password" in record
    assert "raw_binary" in record
    assert "formatted_binary" in record
    assert "num_bits" in record
    assert "entropy" in record
    assert "char_details" in record
    assert "stats" in record

    # Check stats
    stats = record["stats"]
    assert stats["uppercase"] >= 1
    assert stats["lowercase"] >= 1
    assert stats["digits"] >= 1
    assert stats["special"] >= 1

    # Check entropy
    entropy = record["entropy"]
    assert entropy["entropy_bits"] > 80
    assert entropy["tier"] in ("Strong", "Very Strong", "Ultra / Military-Grade", "Quantum-Grade / Unbreakable")
    assert "combinations" in entropy["keyspace_str"]


def test_legacy_hex_mode():
    """Test backward compatibility with hexadecimal generation mode."""
    record = generate_quantum_record(length=16, mode="hex", uppercase_hex=True)
    pwd = record["password"]
    assert len(pwd) == 16
    assert all(c in "0123456789ABCDEF" for c in pwd)
    assert record["mode"] == "hex"


def test_hadamard_circuit_creation():
    """Test quantum circuit creation with Hadamard gates and measurements."""
    circuit = create_hadamard_circuit(num_qubits=4)
    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 4
    gate_names = [inst.operation.name for inst in circuit.data]
    assert "h" in gate_names
    assert "measure" in gate_names


def test_quantum_rng_uniform_int_bounds():
    """Test that QuantumRNG produces integers strictly within [0, upper_bound - 1]."""
    qrng = QuantumRNG(batch_size=8)
    for bound in (2, 5, 10, 26, 94):
        val, bits = qrng.get_uniform_int(bound)
        assert 0 <= val < bound
        assert len(bits) > 0


def test_api_generate_endpoint():
    """Test FastAPI /api/generate endpoint returns valid complex password."""
    from fastapi.testclient import TestClient
    from api.index import app

    client = TestClient(app)
    response = client.get("/api/generate?length=20&uppercase=true&lowercase=true&digits=true&special=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["password"]) == 20
    assert any(c in UPPERCASE_CHARS for c in data["password"])
    assert any(c in LOWERCASE_CHARS for c in data["password"])
    assert any(c in DEFAULT_SPECIAL_CHARS for c in data["password"])
    assert any(c in DIGIT_CHARS for c in data["password"])


def test_api_health_endpoint():
    """Test FastAPI /api/health returns ok status."""
    from fastapi.testclient import TestClient
    from api.index import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_circuit_endpoint():
    """Test FastAPI /api/circuit renders PNG image."""
    from fastapi.testclient import TestClient
    from api.index import app

    client = TestClient(app)
    response = client.get("/api/circuit?num_qubits=4")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 100

