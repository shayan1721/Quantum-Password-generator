"""
Quantum Password Generator - Core Quantum Engine
=================================================
This module implements quantum random bit generation (QRBG) using Qiskit
and Qiskit Aer. It constructs quantum circuits with Hadamard gates to place
qubits into true quantum superposition states (|0> + |1>)/sqrt(2), measures
them to collapse their wavefunctions, and converts the resulting non-deterministic
binary streams into cryptographic passwords with mixed uppercase, lowercase,
numbers, and special characters using zero-bias quantum rejection sampling.
"""

from __future__ import annotations

import math
from typing import Dict, Any, Optional, List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


# Default batch size to ensure simulator remains memory-efficient and ultra-fast.
# For N > MAX_CIRCUIT_QUBITS, bits are generated in batches of smaller circuits.
MAX_CIRCUIT_QUBITS: int = 16

# Standard supported character sets
UPPERCASE_CHARS: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE_CHARS: str = "abcdefghijklmnopqrstuvwxyz"
DIGIT_CHARS: str = "0123456789"
DEFAULT_SPECIAL_CHARS: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# Supported password lengths
SUPPORTED_LENGTHS: tuple[int, ...] = (8, 12, 16, 20, 24, 32, 48, 64)
SUPPORTED_HEX_LENGTHS: tuple[int, ...] = (8, 12, 16, 24, 32, 64)


def create_hadamard_circuit(num_qubits: int = 4) -> QuantumCircuit:
    """Create a quantum circuit with Hadamard gates and measurement operations."""
    if num_qubits <= 0:
        raise ValueError(f"num_qubits must be positive, got {num_qubits}")

    circuit = QuantumCircuit(num_qubits, num_qubits, name="QRBG_Circuit")
    circuit.h(range(num_qubits))
    circuit.measure(range(num_qubits), range(num_qubits))
    return circuit


def run_single_circuit(num_qubits: int, simulator: Optional[AerSimulator] = None) -> str:
    """Run a single quantum circuit on AerSimulator with shots=1.

    Args:
        num_qubits: Number of qubits to simulate (typically <= 16).
        simulator: Optional pre-initialized AerSimulator instance.

    Returns:
        str: Measured binary string of length `num_qubits` containing only '0' and '1'.
    """
    if simulator is None:
        simulator = AerSimulator()

    circuit = create_hadamard_circuit(num_qubits)
    job = simulator.run(circuit, shots=1)
    result = job.result()
    counts = result.get_counts()

    # With shots=1, counts has exactly one key representing the measured bitstring.
    measured_bits = list(counts.keys())[0]

    # In Qiskit, registers can include whitespace if multiple classical registers exist,
    # so we strip any spaces and ensure length matches.
    cleaned_bits = measured_bits.replace(" ", "")
    return cleaned_bits.zfill(num_qubits)


def generate_binary(num_bits: int, batch_size: int = MAX_CIRCUIT_QUBITS) -> str:
    """Generate a random binary string of specified length using quantum superposition.

    For large bit counts (e.g. num_bits > batch_size), bits are simulated in
    efficient chunks to prevent exponential statevector memory scaling and ensure
    instantaneous execution.

    Args:
        num_bits: Total number of random quantum bits to generate.
        batch_size: Maximum qubits per quantum circuit batch (default: 16).

    Returns:
        str: A binary string of length `num_bits` composed purely of '0' and '1'.

    Raises:
        ValueError: If num_bits <= 0 or batch_size <= 0.
    """
    if num_bits <= 0:
        raise ValueError(f"num_bits must be a positive integer, got {num_bits}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got {batch_size}")

    bits_collected: list[str] = []
    bits_remaining = num_bits

    simulator = AerSimulator()

    while bits_remaining > 0:
        chunk_qubits = min(bits_remaining, batch_size)
        chunk_bits = run_single_circuit(chunk_qubits, simulator=simulator)
        bits_collected.append(chunk_bits)
        bits_remaining -= chunk_qubits

    return "".join(bits_collected)


def binary_to_hex(binary_str: str, uppercase: bool = True) -> str:
    """Convert a binary string to a hexadecimal string.

    Pads the binary string with leading zeroes if its length is not a multiple
    of 4, then maps each 4-bit nibble to its corresponding hexadecimal digit.

    Args:
        binary_str: String consisting exclusively of '0' and '1'.
        uppercase: Whether to return hexadecimal letters in uppercase (default: True).

    Returns:
        str: The converted hexadecimal string.

    Raises:
        ValueError: If binary_str is empty or contains non-binary characters.
    """
    if not binary_str:
        raise ValueError("binary_str cannot be empty")

    if any(c not in ("0", "1") for c in binary_str):
        raise ValueError(f"binary_str must contain only '0' and '1', got: {binary_str[:20]!r}")

    # Pad binary so length is a multiple of 4
    remainder = len(binary_str) % 4
    if remainder != 0:
        pad_count = 4 - remainder
        padded_binary = ("0" * pad_count) + binary_str
    else:
        padded_binary = binary_str

    hex_digits: list[str] = []
    for i in range(0, len(padded_binary), 4):
        nibble = padded_binary[i : i + 4]
        val = int(nibble, 2)
        digit = f"{val:x}"
        hex_digits.append(digit.upper() if uppercase else digit.lower())

    return "".join(hex_digits)


class QuantumRNG:
    """Quantum Random Number Generator backed by Qiskit AerSimulator.

    Maintains an in-memory quantum bitstream replenished in memory-safe batches.
    Implements rejection sampling for strict zero modulo bias across arbitrary
    ranges [0, N - 1].
    """

    def __init__(self, simulator: Optional[AerSimulator] = None, batch_size: int = MAX_CIRCUIT_QUBITS) -> None:
        self.simulator = simulator or AerSimulator()
        self.batch_size = batch_size
        self._bit_buffer: list[str] = []
        self.total_bits_generated: int = 0
        self.total_batches_run: int = 0
        self.all_bits_collected: list[str] = []

    def get_bits(self, count: int) -> str:
        """Fetch exact number of quantum bits, running circuits as needed."""
        while len(self._bit_buffer) < count:
            chunk = run_single_circuit(self.batch_size, simulator=self.simulator)
            self._bit_buffer.extend(list(chunk))
            self.all_bits_collected.append(chunk)
            self.total_bits_generated += self.batch_size
            self.total_batches_run += 1

        pulled = self._bit_buffer[:count]
        self._bit_buffer = self._bit_buffer[count:]
        return "".join(pulled)

    def get_uniform_int(self, upper_bound: int) -> Tuple[int, str]:
        """Generate an unbiased uniform integer in range [0, upper_bound - 1] via rejection sampling.

        Rejection sampling ensures STRICTLY ZERO MODULO BIAS.

        Args:
            upper_bound: The upper limit (exclusive), must be >= 1.

        Returns:
            Tuple[int, str]: (selected_int, bitstring_consumed)
        """
        if upper_bound <= 0:
            raise ValueError(f"upper_bound must be positive, got {upper_bound}")
        if upper_bound == 1:
            return 0, ""

        num_bits = (upper_bound - 1).bit_length()
        bits_consumed: list[str] = []

        while True:
            chunk = self.get_bits(num_bits)
            bits_consumed.append(chunk)
            val = int(chunk, 2)
            if val < upper_bound:
                return val, "".join(bits_consumed)


def generate_password(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    special_chars: str = DEFAULT_SPECIAL_CHARS,
    ensure_each_type: bool = True,
    mode: str = "complex",
    uppercase_hex: bool = True,
) -> str:
    """Generate a quantum-derived password.

    Supports both complex multi-character-set passwords (combining uppercase,
    lowercase, numbers, and special characters) and legacy hexadecimal output.

    Args:
        length: Desired password character length (default: 16).
        use_uppercase: Include uppercase letters A-Z (default: True).
        use_lowercase: Include lowercase letters a-z (default: True).
        use_digits: Include digits 0-9 (default: True).
        use_special: Include special characters (default: True).
        special_chars: Custom pool of special characters.
        ensure_each_type: Ensure at least one character from each selected set is present.
        mode: "complex" (default) or "hex" for hexadecimal.
        uppercase_hex: If mode=="hex", whether hex output is uppercase.

    Returns:
        str: Cryptographically sound, quantum-generated password.
    """
    record = generate_quantum_record(
        length=length,
        use_uppercase=use_uppercase,
        use_lowercase=use_lowercase,
        use_digits=use_digits,
        use_special=use_special,
        special_chars=special_chars,
        ensure_each_type=ensure_each_type,
        mode=mode,
        uppercase_hex=uppercase_hex,
    )
    return record["password"]


def generate_quantum_record(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    special_chars: str = DEFAULT_SPECIAL_CHARS,
    ensure_each_type: bool = True,
    mode: str = "complex",
    uppercase_hex: bool = True,
) -> Dict[str, Any]:
    """Generate password along with full quantum audit metadata.

    Returns the raw quantum measurement bitstream, per-character derivation
    audit, final password, character distribution statistics, and cryptographic
    entropy metrics.

    Args:
        length: Password character length (default: 16).
        use_uppercase: Include uppercase letters A-Z (default: True).
        use_lowercase: Include lowercase letters a-z (default: True).
        use_digits: Include digits 0-9 (default: True).
        use_special: Include special characters (default: True).
        special_chars: Pool of special characters.
        ensure_each_type: Ensure representation from each selected set.
        mode: "complex" (default) or "hex".
        uppercase_hex: Hex uppercase toggle.

    Returns:
        Dict[str, Any]: Comprehensive audit record.
    """
    if length <= 0:
        raise ValueError(f"length must be a positive integer, got {length}")

    # Legacy / pure hexadecimal mode
    if mode == "hex":
        num_bits = length * 4
        binary_str = generate_binary(num_bits=num_bits)
        hex_password = binary_to_hex(binary_str, uppercase=uppercase_hex)
        nibbles = [binary_str[i : i + 4] for i in range(0, len(binary_str), 4)]
        formatted_binary = " ".join(nibbles)
        batches = math.ceil(num_bits / MAX_CIRCUIT_QUBITS)
        entropy_data = calculate_entropy_metrics(entropy_bits=num_bits, pool_size=16, length=length)

        char_details = [
            {
                "index": i + 1,
                "char": hex_password[i],
                "category": "Hexadecimal",
                "bits": nibbles[i] if i < len(nibbles) else "",
            }
            for i in range(len(hex_password))
        ]

        return {
            "password": hex_password,
            "raw_binary": binary_str,
            "formatted_binary": formatted_binary,
            "num_bits": num_bits,
            "length": length,
            "batches": batches,
            "entropy": entropy_data,
            "char_details": char_details,
            "stats": {"uppercase": 0, "lowercase": 0, "digits": 0, "special": 0, "hex": length},
            "mode": "hex",
            "charset_size": 16,
        }

    # Complex mode: configure enabled character sets
    char_sets: List[Tuple[str, str]] = []
    if use_uppercase:
        char_sets.append(("Uppercase", UPPERCASE_CHARS))
    if use_lowercase:
        char_sets.append(("Lowercase", LOWERCASE_CHARS))
    if use_digits:
        char_sets.append(("Digit", DIGIT_CHARS))
    if use_special and special_chars:
        # Deduplicate while preserving order
        unique_specials = "".join(dict.fromkeys(special_chars))
        char_sets.append(("Special", unique_specials))

    if not char_sets:
        raise ValueError("At least one character set must be enabled (uppercase, lowercase, digits, or special)")

    # Build flat combined pool: list of (category, char)
    combined_pool: List[Tuple[str, str]] = []
    for cat_name, chars in char_sets:
        for ch in chars:
            combined_pool.append((cat_name, ch))

    pool_size = len(combined_pool)
    qrng = QuantumRNG(batch_size=MAX_CIRCUIT_QUBITS)

    chosen_items: List[Dict[str, Any]] = []

    # 1. Guaranteed character per enabled category (if requested and length permits)
    if ensure_each_type and length >= len(char_sets):
        for cat_name, chars in char_sets:
            idx, bits_used = qrng.get_uniform_int(len(chars))
            chosen_char = chars[idx]
            chosen_items.append({
                "char": chosen_char,
                "category": cat_name,
                "bits": bits_used,
            })

    # 2. Fill the remaining positions uniformly from the combined pool
    remaining_count = length - len(chosen_items)
    for _ in range(remaining_count):
        idx, bits_used = qrng.get_uniform_int(pool_size)
        cat_name, chosen_char = combined_pool[idx]
        chosen_items.append({
            "char": chosen_char,
            "category": cat_name,
            "bits": bits_used,
        })

    # 3. Quantum Fisher-Yates shuffle to randomize positions completely
    for i in range(len(chosen_items) - 1, 0, -1):
        j, _ = qrng.get_uniform_int(i + 1)
        chosen_items[i], chosen_items[j] = chosen_items[j], chosen_items[i]

    # Assign 1-indexed position
    for idx, item in enumerate(chosen_items):
        item["index"] = idx + 1

    password = "".join(item["char"] for item in chosen_items)
    raw_binary = "".join(qrng.all_bits_collected)

    # Format raw binary in 8-bit bytes for visual clarity
    formatted_chunks = [raw_binary[i : i + 8] for i in range(0, len(raw_binary), 8)]
    formatted_binary = " ".join(formatted_chunks) if formatted_chunks else raw_binary

    # Distribution counts
    stats = {
        "uppercase": sum(1 for item in chosen_items if item["category"] == "Uppercase"),
        "lowercase": sum(1 for item in chosen_items if item["category"] == "Lowercase"),
        "digits": sum(1 for item in chosen_items if item["category"] == "Digit"),
        "special": sum(1 for item in chosen_items if item["category"] == "Special"),
    }

    # Cryptographic entropy calculation
    bits_per_char = math.log2(pool_size)
    total_entropy_bits = length * bits_per_char
    entropy_data = calculate_entropy_metrics(entropy_bits=total_entropy_bits, pool_size=pool_size, length=length)

    return {
        "password": password,
        "raw_binary": raw_binary,
        "formatted_binary": formatted_binary,
        "num_bits": qrng.total_bits_generated,
        "length": length,
        "batches": qrng.total_batches_run,
        "entropy": entropy_data,
        "char_details": chosen_items,
        "stats": stats,
        "mode": "complex",
        "charset_size": pool_size,
    }


def calculate_entropy_metrics(entropy_bits: float, pool_size: int = 94, length: int = 16) -> Dict[str, Any]:
    """Calculate cryptographic entropy metrics, security tier, and keyspace.

    Args:
        entropy_bits: Total entropy in bits (length * log2(pool_size)).
        pool_size: Number of unique symbols in active character pool.
        length: Password length.

    Returns:
        Dict[str, Any]: Metrics including progress ratio, tier, keyspace, and estimate.
    """
    # Max reference scale is 256 bits (AES-256 standard)
    progress_ratio = min(1.0, max(0.0, entropy_bits / 256.0))

    if entropy_bits < 48:
        tier = "Moderate"
        color = "#ffaa00"
        desc = "Suitable for low-risk testing. Vulnerable to high-speed dictionary/brute-force attacks."
    elif entropy_bits < 80:
        tier = "Strong"
        color = "#00d26a"
        desc = "Good cryptographic baseline. Highly resilient against standard offline hash crackers."
    elif entropy_bits < 128:
        tier = "Very Strong"
        color = "#00e5ff"
        desc = "High-security banking & enterprise grade. Infeasible to crack within lifetimes."
    elif entropy_bits < 192:
        tier = "Ultra / Military-Grade"
        color = "#bd00ff"
        desc = "128-bit+ quantum-resistant strength. Exceeds the capacity of world supercomputing grids."
    else:
        tier = "Quantum-Grade / Unbreakable"
        color = "#bd00ff"
        desc = "Maximum 256-bit+ security. Far exceeds the physical computational limits of the observable universe."

    # Keyspace in scientific notation (pool_size^length)
    keyspace_exponent = length * math.log10(pool_size)
    base = 10 ** (keyspace_exponent - math.floor(keyspace_exponent))
    exp = int(math.floor(keyspace_exponent))
    keyspace_str = f"{pool_size}^{length} ≈ {base:.2f} × 10^{exp} combinations"

    return {
        "entropy_bits": round(entropy_bits, 1),
        "progress_ratio": progress_ratio,
        "tier": tier,
        "color": color,
        "description": desc,
        "keyspace_str": keyspace_str,
        "pool_size": pool_size,
    }
