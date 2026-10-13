"""
Quantum Password Generator - Streamlit Pure Python UI
=====================================================
A modern, dark-themed interface for generating cryptographic keys
using quantum circuit superposition and wavefunction measurement.
Written strictly in Python without external HTML, CSS, or JS files.
"""

from __future__ import annotations

import datetime
import math
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from quantum_engine import (
    generate_quantum_record,
    create_hadamard_circuit,
    calculate_entropy_metrics,
    SUPPORTED_LENGTHS,
    DEFAULT_SPECIAL_CHARS,
)

# Page configuration
st.set_page_config(
    page_title="Quantum Password Generator",
    page_icon="⚛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def init_session_state() -> None:
    """Initialize in-memory session state variables (never saved to disk)."""
    if "history" not in st.session_state:
        st.session_state.history: List[Dict[str, Any]] = []
    if "current_record" not in st.session_state:
        st.session_state.current_record = None
    if "copied_notice" not in st.session_state:
        st.session_state.copied_notice = False


def format_length_label(length: int) -> str:
    """Return user-friendly label with length, bit count, and security level."""
    # Approximate assuming standard 92-char complex pool (log2(92) ~= 6.52)
    bits = int(length * 6.52)
    if bits < 48:
        level = "Moderate"
    elif bits < 80:
        level = "Strong"
    elif bits < 128:
        level = "Very Strong • Default" if length == 16 else "Very Strong"
    elif bits < 192:
        level = "Ultra (128-bit+)"
    else:
        level = "Quantum-Grade (256-bit+)"
    return f"{length} chars (~{bits} bits — {level})"


def add_to_history(record: Dict[str, Any]) -> None:
    """Append a generated password record to in-memory session history (max 5 items)."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "password": record["password"],
        "length": record["length"],
        "num_bits": record["num_bits"],
        "tier": record["entropy"]["tier"],
        "stats": record.get("stats", {}),
        "raw_binary": record["raw_binary"],
    }
    # Keep only the last 5 records
    st.session_state.history.insert(0, entry)
    if len(st.session_state.history) > 5:
        st.session_state.history.pop()


def render_header() -> None:
    """Render the application title, badge, and explanatory subtitle."""
    st.title("⚛️ Quantum Password Generator")
    st.subheader("Cryptographic keys powered by true quantum superposition")
    st.write(
        "Generate unguessable passwords by simulating Hadamard quantum circuits with "
        "Qiskit Aer. Combines uppercase letters, lowercase letters, numbers, and special "
        "characters with zero modulo bias, derived directly from quantum wavefunction collapse."
    )
    st.divider()


def render_controls() -> tuple[int, bool, bool, bool, bool, str, bool, str]:
    """Render password configuration controls.

    Returns:
        tuple containing:
        - selected_length: int
        - use_uppercase: bool
        - use_lowercase: bool
        - use_digits: bool
        - use_special: bool
        - special_chars: str
        - ensure_each_type: bool
        - mode: str
    """
    st.markdown("### ⚙️ Generation Settings")

    col_len, col_preset = st.columns([3, 2])

    with col_preset:
        preset = st.selectbox(
            label="Security Preset:",
            options=[
                "⚛️ Quantum Complex (Upper + Lower + Numbers + Symbols)",
                "🔤 Quantum Alphanumeric (Upper + Lower + Numbers)",
                "🔑 Quantum Hexadecimal (0–9, A–F)",
                "🛠️ Custom Character Mix",
            ],
            index=0,
            help="Choose a preconfigured security profile or customize individual character sets.",
        )

    with col_len:
        default_index = SUPPORTED_LENGTHS.index(16) if 16 in SUPPORTED_LENGTHS else 2
        selected_length = st.selectbox(
            label="Password Length:",
            options=SUPPORTED_LENGTHS,
            index=default_index,
            format_func=format_length_label,
            help="Total characters in the generated password. Longer lengths provide exponential keyspace scaling.",
        )

    # Determine defaults based on preset
    if "Hexadecimal" in preset:
        mode = "hex"
        use_uppercase = True
        use_lowercase = False
        use_digits = True
        use_special = False
        special_chars = ""
        ensure_each_type = False
        st.info("ℹ️ Hexadecimal mode active: generates base-16 strings (0–9, A–F) mapping 4 quantum bits per character.")
    else:
        mode = "complex"
        if "Alphanumeric" in preset:
            default_upper = True
            default_lower = True
            default_digits = True
            default_special = False
        elif "Custom" in preset:
            default_upper = True
            default_lower = True
            default_digits = True
            default_special = True
        else:
            # Complex default: combination of upper, lower, digits, and special characters
            default_upper = True
            default_lower = True
            default_digits = True
            default_special = True

        st.markdown("**Character Sets to Integrate:**")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            use_uppercase = st.checkbox("🔠 Uppercase (A-Z)", value=default_upper, key="chk_upper")
        with col_c2:
            use_lowercase = st.checkbox("🔡 Lowercase (a-z)", value=default_lower, key="chk_lower")
        with col_c3:
            use_digits = st.checkbox("🔢 Numbers (0-9)", value=default_digits, key="chk_digits")
        with col_c4:
            use_special = st.checkbox("✨ Symbols (!@#$)", value=default_special, key="chk_special")

        special_chars = DEFAULT_SPECIAL_CHARS
        if use_special:
            with st.expander("🔧 Customize Special Characters", expanded=False):
                special_chars = st.text_input(
                    "Special Characters Pool:",
                    value=DEFAULT_SPECIAL_CHARS,
                    help="You can add or remove specific symbols to conform to specific password policies.",
                )

        col_guarantee, _ = st.columns([3, 1])
        with col_guarantee:
            ensure_each_type = st.checkbox(
                "🛡️ Guarantee at least one character of each enabled type",
                value=True,
                help="Ensures that mixed uppercase, lowercase, numbers, and symbols are all present in the output.",
            )

    return (
        selected_length,
        use_uppercase,
        use_lowercase,
        use_digits,
        use_special,
        special_chars,
        ensure_each_type,
        mode,
    )


def render_results(record: Dict[str, Any]) -> None:
    """Display the three clearly separated results, strength indicator, and copy actions."""
    entropy = record["entropy"]
    password = record["password"]
    raw_binary = record["raw_binary"]
    formatted_binary = record["formatted_binary"]
    num_bits = record["num_bits"]
    batches = record["batches"]
    stats = record.get("stats", {})
    char_details = record.get("char_details", [])

    st.markdown("---")
    st.markdown("## 🎯 Generated Results")

    # ---------------------------------------------------------
    # Result 3 (Prominently displayed first for user convenience)
    # ---------------------------------------------------------
    st.markdown("### 🔑 3. Final Quantum Password")
    st.caption("Ready for immediate use. Click the copy icon in the code box or use the button below.")
    st.code(password, language="text")

    # Character composition pills
    if record.get("mode") != "hex":
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric(label="🔠 Uppercase", value=f"{stats.get('uppercase', 0)}")
        with col_s2:
            st.metric(label="🔡 Lowercase", value=f"{stats.get('lowercase', 0)}")
        with col_s3:
            st.metric(label="🔢 Digits", value=f"{stats.get('digits', 0)}")
        with col_s4:
            st.metric(label="✨ Special", value=f"{stats.get('special', 0)}")

    col_copy, col_clear = st.columns([2, 2])
    with col_copy:
        if st.button("📋 Confirm Password Copied", key="copy_btn", use_container_width=True):
            st.session_state.copied_notice = True

    with col_clear:
        if st.button("🔄 Generate Another", key="regen_btn", use_container_width=True):
            st.rerun()

    if st.session_state.copied_notice:
        st.success(f"Password ({len(password)} chars) ready in memory!")

    # ---------------------------------------------------------
    # Password Strength & Entropy Section
    # ---------------------------------------------------------
    st.markdown("### 🛡️ Entropy & Strength Evaluation")
    st.progress(
        value=entropy["progress_ratio"],
        text=f"Cryptographic Entropy: {entropy['entropy_bits']} bits / 256 bits ({entropy['tier']})",
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="Total Entropy", value=f"{entropy['entropy_bits']} bits", delta="True Quantum")
    with col_m2:
        st.metric(label="Security Tier", value=entropy["tier"])
    with col_m3:
        st.metric(label="Character Pool", value=f"{entropy.get('pool_size', 92)} chars")
    with col_m4:
        st.metric(label="Circuits Executed", value=f"{batches} batch(es)")

    st.info(f"**Keyspace:** {entropy['keyspace_str']}\n\n**Evaluation:** {entropy['description']}")

    # ---------------------------------------------------------
    # Result 2: Quantum Entropy to Character Derivation
    # ---------------------------------------------------------
    st.markdown("### 🔠 2. Quantum Entropy to Character Mapping")
    st.caption(
        "Each character is selected using zero-bias quantum rejection sampling. "
        "Quantum bits collapse from superposition states and map directly into the chosen character."
    )

    # Show clean breakdown table/chips of character mappings
    if char_details:
        sample_chars = char_details[:16]
        items_preview = "  |  ".join(
            f"#{item['index']}: '{item['char']}' [{item['category'][:3]}]"
            for item in sample_chars
        )
        if len(char_details) > 16:
            items_preview += f"  |  ... ({len(char_details) - 16} more)"
        st.code(items_preview, language="text")

    # ---------------------------------------------------------
    # Result 1: Raw Quantum Measurement (Binary)
    # ---------------------------------------------------------
    st.markdown("### ⚡ 1. Raw Quantum Measurement (Binary)")
    st.caption(
        f"Simulated across {batches} circuit batch(es). Exactly {num_bits} non-deterministic "
        "bits collapsed from quantum superposition states |+⟩ via AerSimulator."
    )
    with st.container():
        st.code(formatted_binary, language="text")
        st.caption(f"Continuous bitstream ({len(raw_binary)} bits measured): `{raw_binary[:64]}...`")


def render_history() -> None:
    """Render the in-memory history of the last 5 passwords generated in this session."""
    st.markdown("---")
    st.markdown("### 📜 Session History (Last 5 Passwords)")
    st.caption("Stored purely in active server session memory. Never written to disk or logs.")

    if not st.session_state.history:
        st.write("No passwords generated in this session yet.")
        return

    for idx, item in enumerate(st.session_state.history):
        with st.container():
            col_info, col_pwd = st.columns([1, 2])
            with col_info:
                stats = item.get("stats", {})
                breakdown = ""
                if stats:
                    breakdown = f" (🔠{stats.get('uppercase',0)} 🔡{stats.get('lowercase',0)} 🔢{stats.get('digits',0)} ✨{stats.get('special',0)})"
                st.write(
                    f"**#{idx + 1}** — `{item['timestamp']}`\n\n"
                    f"{item['length']} chars • {item['tier']}{breakdown}"
                )
            with col_pwd:
                st.code(item["password"], language="text")

    if st.button("🗑️ Clear Session History", key="clear_hist_btn"):
        st.session_state.history = []
        st.rerun()


def render_how_it_works() -> None:
    """Render collapsible educational section with circuit drawing and quantum theory."""
    with st.expander("🔬 How It Works: Quantum Superposition & True Randomness", expanded=False):
        st.markdown(
            """
            ### 1. Quantum Random Bit Generation (QRBG)
            Traditional computer random number generators (PRNGs) are deterministic: given the same 
            seed, they produce the identical sequence. 

            In quantum mechanics, measurement outcomes are fundamentally non-deterministic:
            - **Ground State:** Each qubit is initialized to state $|0\\rangle$.
            - **Hadamard Gate ($H$):** Creates an equal superposition:
              $$|\\psi\\rangle = H|0\\rangle = \\frac{1}{\\sqrt{2}}(|0\\rangle + |1\\rangle)$$
            - **Wavefunction Collapse:** When measured, the wavefunction collapses into either 
              $|0\\rangle$ or $|1\\rangle$ with strictly equal probability ($P=0.5$), governed by the **Born Rule**.
            - **AerSimulator Execution:** We execute this circuit with `shots=1`, yielding truly 
              unpredictable binary strings.
            - **Zero Modulo Bias:** Rejection sampling ensures every character in the combined pool 
              has mathematically equal probability, preventing modulo bias attacks.
            """
        )

        st.markdown("### 2. Quantum Circuit Architecture (4-Qubit Sample)")
        try:
            # Draw circuit with Qiskit and Matplotlib
            circuit = create_hadamard_circuit(num_qubits=4)
            fig = circuit.draw(output="mpl", style="iqp-dark")
            # Ensure background matches dark theme
            fig.patch.set_facecolor("#1a1f2c")
            st.pyplot(fig)
            plt.close(fig)
        except Exception:
            # Clean fallback to text diagram if graphics backend encounters issues
            circuit = create_hadamard_circuit(num_qubits=4)
            text_circuit = circuit.draw(output="text")
            st.text(str(text_circuit))

        st.markdown(
            """
            ### 3. Memory-Safe Batching for High Security Keys
            A full 256-bit quantum statevector would theoretically require $2^{256}$ complex numbers 
            (more values than atoms in the universe). 

            To simulate arbitrarily large keys instantaneously with zero memory strain, the engine 
            partitions the request into batches of $\\le 16$ qubits on AerSimulator and concatenates 
            the resulting quantum measurements.
            """
        )


def main() -> None:
    """Main application loop."""
    init_session_state()
    render_header()

    (
        selected_length,
        use_uppercase,
        use_lowercase,
        use_digits,
        use_special,
        special_chars,
        ensure_each_type,
        mode,
    ) = render_controls()

    st.markdown("")
    generate_pressed = st.button(
        "⚡ Generate Quantum Password",
        type="primary",
        use_container_width=True,
    )

    if generate_pressed:
        st.session_state.copied_notice = False
        try:
            with st.spinner("⚛️ Collapsing quantum superposition on AerSimulator..."):
                record = generate_quantum_record(
                    length=selected_length,
                    use_uppercase=use_uppercase,
                    use_lowercase=use_lowercase,
                    use_digits=use_digits,
                    use_special=use_special,
                    special_chars=special_chars,
                    ensure_each_type=ensure_each_type,
                    mode=mode,
                )
                st.session_state.current_record = record
                add_to_history(record)
        except Exception as exc:
            st.error(f"❌ Error during quantum circuit execution: {exc}")

    if st.session_state.current_record:
        render_results(st.session_state.current_record)

    render_history()
    render_how_it_works()


if __name__ == "__main__":
    main()
