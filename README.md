# ⚛️ Quantum Password Generator

A high-entropy, cryptographically sound quantum password generator built with **Qiskit**, featuring dual deployment targets:
1. **Local / Streamlit Community Cloud Application** (Pure Python Streamlit UI)
2. **Vercel Serverless Web Application** (FastAPI backend + Modern Dark Web UI)

Unlike standard pseudo-random number generators (PRNGs) that rely on deterministic mathematical seeds, this application derives true physical non-determinism from simulated quantum superposition states ($|+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$) and wavefunction collapse.

---

## 🚀 Key Features

- **Mixed Uppercase & Lowercase in the Same Output:** Integrates uppercase letters (`A–Z`) and lowercase letters (`a–z`) seamlessly in every generated password.
- **Special Characters Integration:** Natively incorporates special characters (`!@#$%^&*()_+-=[]{}|;:,.<>?`) with customizable symbol pools.
- **Full Alphanumeric + Symbolic Support:** Generates passwords with any combination of Uppercase, Lowercase, Numbers (`0–9`), and Special Characters.
- **Zero Modulo Bias (Rejection Sampling):** Uses quantum rejection sampling to map quantum bits uniformly across character pools, eliminating cryptographic modulo bias.
- **True Quantum Superposition:** Simulates Hadamard circuits on Qiskit Aer (`AerSimulator`) with measurement-driven wavefunction collapse governed by the Born Rule ($P = 0.5$).
- **Memory-Efficient Batching:** Partitions large entropy requests into lightweight $\le 16$-qubit quantum circuit batches to ensure rapid, zero-RAM-strain execution.
- **Three Clearly Separated Results:**
  1. **Raw Quantum Measurement (Binary):** The exact bitstream measured from quantum register collapse.
  2. **Quantum Entropy to Character Mapping:** Transparent mapping showing how measured quantum bits collapsed into each character and category.
  3. **Final Quantum Password:** Copy-ready code box with one-click clipboard confirmation and character composition metrics.
- **Cryptographic Strength & Keyspace Analysis:** Live progress bar, entropy bit calculation ($L \times \log_2(K)$), and scientific notation keyspace analysis ($K^L$ combinations).
- **Session History:** In-memory tracking of the last 5 passwords (never written to disk or logs).
- **Interactive "How It Works" Section:** Live Qiskit quantum circuit diagram rendered with Matplotlib.

---

## 📦 Project Structure

```text
quantum-password-generator/
├── api/
│   └── index.py            # FastAPI Serverless backend for Vercel & local REST API
├── public/
│   └── index.html          # Modern dark-themed responsive web UI
├── vercel.json             # Vercel routing and serverless rewrites
├── quantum_engine.py       # Core quantum engine with rejection sampling & QRBG pipeline
├── app.py                  # Streamlit UI (for local run or Streamlit Cloud)
├── test_engine.py          # Pytest suite (15 tests: engine, character mix, API)
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Pinned dependencies
├── .gitignore              # Ignores .venv, cache, and temporary files
├── README.md               # Project documentation
└── .streamlit/
    └── config.toml         # Dark theme configuration for Streamlit
```

---

## 🖥️ Running Locally

### 1. Setup Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Option A: Run Streamlit UI (Recommended)
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

### 3. Option B: Run FastAPI Backend & Web UI
```bash
python -m uvicorn api.index:app --reload --port 8000
```
- Web UI: Open `http://localhost:8000/public/index.html`
- API docs: Open `http://localhost:8000/docs`
- Generate endpoint: `http://localhost:8000/api/generate?length=16`

---

## 🧪 Running Tests

Execute the comprehensive test suite with `pytest`:

```bash
pytest -v
```

All 15 tests verify:
- Quantum circuit construction & Hadamard gate placement
- Random bitstream generation & batching
- Combined uppercase & lowercase generation in the same output
- Special characters integration
- Coexistence of all 4 character types (upper, lower, digits, symbols)
- Custom special character pools
- Zero-bias rejection sampling integer bounds
- Quantum record metadata & entropy calculations
- Legacy hexadecimal mode backward compatibility
- FastAPI endpoints (`/api/generate`, `/api/health`, `/api/circuit`)

---

## 🌐 Deploying to Vercel

1. Push this repository to GitHub.
2. In [Vercel Dashboard](https://vercel.com/dashboard), import the repository.
3. Keep default settings (`vercel.json` automatically configures the Python serverless runtime and public frontend).
4. Click **Deploy**.

---

## 🛡️ Security & Privacy Notice

- **Ephemeral Storage:** Generated passwords and session histories reside strictly within memory. No passwords, bitstreams, or keys are ever saved to disk, databases, or log files.
- **True Entropy:** Powered by the physical randomness of quantum superposition states simulated via Qiskit Aer.
