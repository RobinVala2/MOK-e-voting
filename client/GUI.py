import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QSpinBox, QFormLayout, QGroupBox, QMessageBox, QProgressDialog, QScrollArea,
    QSplitter, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from .hyperion_runner import run_hyperion as hyperion_run

LAST_BB = None

class HyperionWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, voters, tellers, threshold, max_votes, use_pqc, project_root):
        super().__init__()
        self.voters = voters
        self.tellers = tellers
        self.threshold = threshold
        self.max_votes = max_votes
        self.use_pqc = use_pqc
        self.project_root = project_root
        self.old_cwd = os.getcwd()
    
    def run(self):
        try:
            os.chdir(self.project_root)
            result = hyperion_run(
                voters=self.voters,
                tellers=self.tellers,
                threshold=self.threshold,
                max_votes=self.max_votes,
                use_pqc=self.use_pqc
            )
            os.chdir(self.old_cwd)
            self.finished.emit({
                "tally": result["bulletin_board"],
                "timings": result["timings"],
            })
        except Exception as e:
            os.chdir(self.old_cwd)
            self.error.emit(str(e))


def format_vote_display(vote_str):
    """
    Format vote string to display x and y on separate lines.
    Input: "{'x': 123, 'y': 456, 'curve': 'P-256'}"
    Output: "x: 123\ny: 456\ncurve: P-256"
    """
    if not vote_str or not isinstance(vote_str, str):
        return vote_str
    
    x_match = re.search(r"'x':\s*(\d+)", vote_str)
    y_match = re.search(r"'y':\s*(\d+)", vote_str)
    curve_match = re.search(r"'curve':\s*'([^']+)'", vote_str)
    
    if x_match and y_match:
        x_val = x_match.group(1)
        y_val = y_match.group(1)
        curve_val = curve_match.group(1) if curve_match else "P-256"
        
        return f"x: {x_val}\ny: {y_val}\ncurve: {curve_val}"
    
    return vote_str


def get_bb_direct():
    """
    Get bulletin board from local storage.
    """
    if LAST_BB:
        return {"status": "ok", "bb": LAST_BB}
    return {"status": "error", "detail": "No bulletin board available. Run Hyperion first."}


class GUIApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyperion GUI")
        self.resize(1100, 700)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tab_tally = QWidget()
        self.tab_tally.setLayout(self.build_tally_tab())
        self.tabs.addTab(self.tab_tally, "Hyperion Protocol")

        self.tab_bb = QWidget()
        self.tab_bb.setLayout(self.build_bb_tab())
        self.tabs.addTab(self.tab_bb, "Bulletin Board")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def build_tally_tab(self):
        layout = QVBoxLayout()
        
        # Settings group
        settings_group = QGroupBox("Hyperion Protocol Settings")
        settings_layout = QFormLayout()
        
        # Number of Voters
        self.spin_voters = QSpinBox()
        self.spin_voters.setMinimum(1)
        self.spin_voters.setMaximum(100000)
        self.spin_voters.setValue(50)
        settings_layout.addRow("Number of Voters:", self.spin_voters)
        
        # Number of Tellers
        self.spin_tellers = QSpinBox()
        self.spin_tellers.setMinimum(1)
        self.spin_tellers.setMaximum(100)
        self.spin_tellers.setValue(3)
        settings_layout.addRow("Number of Tellers:", self.spin_tellers)
        
        # Threshold
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setMinimum(1)
        self.spin_threshold.setMaximum(100)
        self.spin_threshold.setValue(2)
        self.spin_tellers.valueChanged.connect(
            lambda v: self.spin_threshold.setMaximum(v)
        )
        settings_layout.addRow("Threshold (K):", self.spin_threshold)
        
        # Max Votes
        self.spin_max_votes = QSpinBox()
        self.spin_max_votes.setMinimum(2)
        self.spin_max_votes.setMaximum(100)
        self.spin_max_votes.setValue(2)
        settings_layout.addRow("Max Vote Value:", self.spin_max_votes)
        
        self.chk_pqc = QCheckBox("Enable Post-Quantum Cryptography (ML-DSA)")
        self.chk_pqc.setToolTip(
            "When enabled, replaces ECDSA signatures with ML-DSA.\n\n"
        )
        settings_layout.addRow("", self.chk_pqc)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        self.btn_tally = QPushButton("Run Hyperion Protocol")
        self.btn_tally.clicked.connect(self.do_tally)

        self.btn_tally.setToolTip(
            "Runs full Hyperion protocol.\n\n"
            "Classical: EC-ElGamal encryption, ECDSA signatures.\n\n"
            "PQC alternative: ML-KEM (encryption) + ML-DSA (signatures)."
        )

        self.table_tally = QTableWidget()
        self.table_tally.setColumnCount(3)
        self.table_tally.setHorizontalHeaderLabels(["Voter ID", "Vote", "Commitment"])
        self.table_tally.verticalHeader().setVisible(False)
        self.table_tally.horizontalHeader().setStretchLastSection(True)
        self.table_tally.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_tally.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_tally.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.btn_tally)
        layout.addWidget(self.table_tally)

        self.stats_label = QLabel("Performance Statistics (seconds)")
        self.stats_label.hide()
        layout.addWidget(self.stats_label)
        
        self.table_stats = QTableWidget()
        self.table_stats.setRowCount(1)
        self.table_stats.setVerticalHeaderLabels(["Time (seconds)"])
        self.table_stats.verticalHeader().setVisible(True)
        self.table_stats.horizontalHeader().setStretchLastSection(True)
        self.table_stats.setFixedHeight(60) 
        self.table_stats.setRowHeight(0, 30) 
        self.table_stats.hide()
        layout.addWidget(self.table_stats)

        return layout

    def build_bb_tab(self):
        layout = QVBoxLayout()
        
        splitter = QSplitter(Qt.Vertical)
        
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Hyperion Protocol: How Results Are Computed")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)

        content_layout = QHBoxLayout()
        
        diagram_frame = QFrame()
        diagram_frame.setFrameStyle(QFrame.StyledPanel)
        diagram_layout = QVBoxLayout(diagram_frame)
        
        diagram_label = QLabel("Protocol Sequence")
        diagram_label.setFont(QFont("", 10, QFont.Bold))
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_layout.addWidget(diagram_label)
        
        self.seq_diagram = QLabel()
        self.seq_diagram.setAlignment(Qt.AlignCenter)
        diagram_path = os.path.join(PROJECT_ROOT, "diagrams", "seq2_update.png")
        if os.path.exists(diagram_path):
            pixmap = QPixmap(diagram_path)
            scaled_pixmap = pixmap.scaledToWidth(350, Qt.SmoothTransformation)
            self.seq_diagram.setPixmap(scaled_pixmap)
        else:
            self.seq_diagram.setText("(Sequence diagram not found)")
        
        scroll_diagram = QScrollArea()
        scroll_diagram.setWidget(self.seq_diagram)
        scroll_diagram.setWidgetResizable(True)
        scroll_diagram.setMinimumWidth(380)
        scroll_diagram.setMaximumWidth(400)
        diagram_layout.addWidget(scroll_diagram)
        content_layout.addWidget(diagram_frame)
        
        explanation_frame = QFrame()
        explanation_frame.setFrameStyle(QFrame.StyledPanel)
        explanation_layout = QVBoxLayout(explanation_frame)
        
        explanation_title = QLabel("Computation Process")
        explanation_title.setFont(QFont("", 10, QFont.Bold))
        explanation_layout.addWidget(explanation_title)
        
        self.explanation_text = QTextEdit()
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setMinimumHeight(200)
        self.explanation_text.setHtml(self._get_protocol_explanation())
        explanation_layout.addWidget(self.explanation_text)
        
        content_layout.addWidget(explanation_frame, 1)
        top_layout.addLayout(content_layout)
        
        splitter.addWidget(top_widget)
        
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 10, 0, 0)
        
        results_header = QHBoxLayout()
        results_title = QLabel("Final Bulletin Board Results")
        results_title.setFont(QFont("", 12, QFont.Bold))
        results_header.addWidget(results_title)
        
        btn_refresh = QPushButton("Refresh BB")
        btn_refresh.clicked.connect(self.do_show_bb)
        btn_refresh.setToolTip(
            "Displays the final bulletin board.\n\n"
            "Classical: EC-ElGamal commitments.\n"
            "PQC alternative: ML-KEM or lattice-based commitments."
        )
        btn_refresh.setMaximumWidth(120)
        results_header.addWidget(btn_refresh)
        results_header.addStretch()
        
        bottom_layout.addLayout(results_header)
        
        data_explanation = QLabel(
            "<b>Vote:</b> Elliptic curve point (x, y) representing the encrypted vote after threshold decryption. "
            "<b>Commitment:</b> Base64-encoded cryptographic commitment used for verification."
        )
        data_explanation.setWordWrap(True)
        data_explanation.setStyleSheet("color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        bottom_layout.addWidget(data_explanation)
        
        self.table_bb = QTableWidget()
        self.table_bb.setColumnCount(3)
        self.table_bb.setHorizontalHeaderLabels(
            ["Voter ID", "Vote (Decrypted Point)", "Commitment (Base64)"]
        )
        self.table_bb.verticalHeader().setVisible(False)  
        self.table_bb.horizontalHeader().setStretchLastSection(True)
        self.table_bb.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_bb.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_bb.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        bottom_layout.addWidget(self.table_bb)
        
        splitter.addWidget(bottom_widget)

        splitter.setSizes([350, 350])
        
        layout.addWidget(splitter)
        return layout
    
    def _get_protocol_explanation(self):
        return """
        <style>
            body { font-family: Arial, sans-serif; font-size: 11px; background-color: white; color: #000; }
            h3 { color: #1a5276; margin-bottom: 5px; margin-top: 15px; }
            .phase { margin-bottom: 10px; padding: 8px; background-color: white; border-left: 3px solid #3498db; }
            .phase-title { font-weight: bold; color: #2980b9; }
            .crypto { color: #1a5276; font-family: monospace; font-weight: bold; }
            .pqc { color: #5dade2; font-family: monospace; font-weight: bold; }
            .pqc-note { color: #2874a6; font-style: italic; margin-top: 3px; }
            ul { margin: 5px 0; padding-left: 20px; }
            li { margin: 3px 0; color: #000; }
            .mapping { color: #555; margin-left: 15px; }
            table { border-collapse: collapse; width: 100%; margin: 8px 0; background-color: white; }
            th { background-color: #3498db; color: white; padding: 5px; text-align: left; }
            td { padding: 4px; border-bottom: 1px solid #ddd; background-color: white; color: #000; }
            tr:nth-child(even) { background-color: white; }
        </style>
        
        <h3>How Hyperion Computes Voting Results</h3>
        
        <div class="phase">
            <span class="phase-title">1. Setup Phase</span>
            <ul>
                <li>Generate <span class="crypto">threshold key shares</span> for T tellers using Shamir's Secret Sharing</li>
                <li>Create a shared <span class="crypto">EC-ElGamal public key</span> (P-256 curve)</li>
                <li>At least K of T tellers needed to decrypt (threshold = K)</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">Threshold ML-KEM</span> (research) replaces EC-ElGamal threshold encryption</div>
        </div>
        
        <div class="phase">
            <span class="phase-title">2. Voting Phase</span>
            <ul>
                <li>Each voter generates a <span class="crypto">trapdoor keypair</span> (secret x, public h=xG)</li>
                <li>Vote value v is encoded as point: <span class="crypto">M = vG</span></li>
                <li>Encrypted using <span class="crypto">EC-ElGamal</span>: C = (rG, rY + M)</li>
                <li>Voter signs ballot with <span class="crypto">ECDSA</span> signature</li>
                <li>Generates <span class="crypto">NIZK + Chaum-Pedersen</span> proofs (Fiat-Shamir transform)</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">ML-KEM + symmetric DEM</span> (encryption), <span class="pqc">ML-DSA</span> (signatures), <span class="pqc">Lattice-based Sigma protocols + Fiat–Shamir with aborts</span> (ZK proofs)</div>
        </div>
        
        <div class="phase">
            <span class="phase-title">3. Tallying Phase</span>
            <ul>
                <li><b>Ballot Validation:</b> Verify <span class="crypto">ECDSA signatures</span> and <span class="crypto">Sigma protocols</span></li>
                <li><b>Mixnet Shuffling:</b> <span class="crypto">ElGamal-compatible</span> Terelius-Wikström mixnet</li>
                <li><b>Threshold Decryption:</b> Partial decryptions with <span class="crypto">Lagrange interpolation</span></li>
                <li>Result: Decrypted vote points on the final bulletin board</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">Threshold ML-KEM</span> (decryption), <span class="pqc">Ring-LWE shuffle</span> (mixnet), <span class="pqc">Lattice-based Sigma protocols +Fiat-Shamir with aborts</span> (proofs)</div>
        </div>
        
        <div class="phase">
            <span class="phase-title">4. Notification Phase</span>
            <ul>
                <li>Compute voter-specific term: <span class="crypto">g^r = ∏(g^r_i)</span> from all tellers</li>
                <li>Send <span class="crypto">EC-ElGamal encrypted</span> notification to each voter</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">ML-KEM + symmetric DEM</span> replaces EC-ElGamal for notifications</div>
        </div>
        
        <div class="phase">
            <span class="phase-title">5. Verification Phase</span>
            <ul>
                <li>Voter computes commitment: <span class="crypto">g^(r·x)</span> using their trapdoor key</li>
                <li>Looks up their vote on the bulletin board by matching <span class="crypto">EC-ElGamal commitment</span></li>
                <li>Verifies vote was recorded correctly</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">Lattice-based Sigma protocols + Fiat–Shamir with aborts</span> for commitment verification</div>
        </div>
        
        <div class="phase">
            <span class="phase-title">6. Coercion Mitigation & Individual Views</span>
            <ul>
                <li>Voters can produce <span class="crypto">fake dual keys</span> that "verify" to a different vote</li>
                <li>Individual views use <span class="crypto">EC-ElGamal re-encryption</span> shuffle</li>
            </ul>
            <div class="pqc-note">PQC: <span class="pqc">Lattice-based Sigma protocols + Fiat–Shamir with aborts</span> for coercion mitigation and individual views</div>
        </div>
        
        <h3>Post-Quantum Cryptography Mapping</h3>
        <table>
            <tr><th>Component</th><th>Classical (Current)</th><th>PQC Alternative</th></tr>
            <tr><td>Vote Encryption</td><td>EC-ElGamal</td><td><span class="pqc">ML-KEM + symmetric DEM</span></td></tr>
            <tr><td>Digital Signatures</td><td>ECDSA</td><td><span class="pqc">ML-DSA</span></td></tr>
            <tr><td>Zero-Knowledge Proofs</td><td>NIZK + Chaum-Pedersen + Fiat-Shamir</td><td><span class="pqc">Lattice-based Sigma protocols + FS-with-aborts / zk-STARKs</span></td></tr>
            <tr><td>Threshold Decryption</td><td>EC-ElGamal threshold</td><td><span class="pqc">Threshold ML-KEM (research)</span></td></tr>
            <tr><td>Mixnet Shuffle</td><td>ElGamal-compatible (Terelius-Wikström)</td><td><span class="pqc">Ring-LWE shuffle (research)</span></td></tr>
            <tr><td>Hash Functions</td><td>SHA-256</td><td><span class="pqc">SHA-3 / SHAKE-256</span></td></tr>
        </table>
        
        <h3>Understanding the Output</h3>
        <p><b>Vote (x, y, curve):</b> The decrypted elliptic curve point representing the vote. 
        The actual vote value v can be recovered by computing discrete log: find v where vG = (x,y).</p>
        <p><b>Commitment:</b> A cryptographic binding (<span class="crypto">SHA-256</span> based, PQC: <span class="pqc">SHA-3</span>) 
        that allows voters to verify their vote without revealing how they voted. Derived from trapdoor keys and teller random values.</p>
        """

    def do_tally(self):
        # Get settings from spin boxes
        voters = self.spin_voters.value()
        tellers = self.spin_tellers.value()
        threshold = self.spin_threshold.value()
        max_votes = self.spin_max_votes.value()
        use_pqc = self.chk_pqc.isChecked()

        # Validate threshold <= tellers
        if threshold > tellers:
            QMessageBox.warning(self, "Invalid Settings", 
                              f"Threshold ({threshold}) cannot be greater than number of tellers ({tellers})")
            return

        mode_text = "PQC Mode (ML-DSA-65)" if use_pqc else "Classical Mode (ECDSA)"
        self.progress = QProgressDialog(f"Running Hyperion Protocol...\n{mode_text}", None, 0, 0, self)
        self.progress.setWindowTitle("Please Wait")
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.setMinimumWidth(300)
        self.progress.setMinimumDuration(0)
        self.progress.show()
        
        self.worker = HyperionWorker(voters, tellers, threshold, max_votes, use_pqc, PROJECT_ROOT)
        self.worker.finished.connect(self._on_hyperion_finished)
        self.worker.start()
    
    def _on_hyperion_finished(self, res):
        global LAST_BB
        self.progress.close()
        LAST_BB = res.get("tally", [])
        
        # Populate tally table
        tally_rows = res.get("tally", [])
        self.table_tally.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_tally.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_tally.setRowHeight(row_idx, 80)
            self.table_tally.setItem(row_idx, 1, vote_item)
            self.table_tally.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))

        # Populate Bulletin Board
        self.table_bb.setRowCount(len(tally_rows))
        for row_idx, row in enumerate(tally_rows):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_bb.setRowHeight(row_idx, 80)
            self.table_bb.setItem(row_idx, 1, vote_item)
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))

        # Populate Timing Statistics table
        timings = res.get("timings", {})
        if timings:
            timing_phases = [
                ("Setup", "Setup"),
                ("Voting (avg.)", "Voting (avg.)"),
                ("Tallying (Mixing)", "Tallying (Mixing)"),
                ("Tallying (Decryption)", "Tallying (Decryption)"),
                ("Notification", "Notification"),
                ("Verification (avg.)", "Verification (avg.)"),
                ("Coercion Mitigation", "Coercion Mitigation"),
                ("Individual Views", "Individual Views"),
            ]
            
            available_phases = [(key, name) for key, name in timing_phases if key in timings]
            
            if available_phases:
                self.table_stats.setColumnCount(len(available_phases))
                self.table_stats.setHorizontalHeaderLabels([name for _, name in available_phases])
                
                for col_idx in range(len(available_phases)):
                    self.table_stats.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeToContents)
                
                for col_idx, (key, name) in enumerate(available_phases):
                    value = timings[key]
                    try:
                        formatted_value = f"{float(value):.3f}"
                    except (ValueError, TypeError):
                        formatted_value = str(value)
                    
                    self.table_stats.setItem(0, col_idx, QTableWidgetItem(formatted_value))
                
                self.table_stats.setRowHeight(0, 30)
                self.table_stats.setFixedHeight(60) 
                
                self.stats_label.show()
                self.table_stats.show()
            else:
                self.stats_label.hide()
                self.table_stats.hide()
        else:
            self.stats_label.hide()
            self.table_stats.hide()

    def do_show_bb(self):
        res = get_bb_direct()
        
        if res.get("status") != "ok":
            QMessageBox.warning(self, "No Data", res.get("detail", "No bulletin board available. Run Hyperion first."))
            return

        bb = res.get("bb", [])
        self.table_bb.setRowCount(len(bb))
        for row_idx, row in enumerate(bb):
            self.table_bb.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            vote_str = format_vote_display(row.get("vote", ""))
            vote_item = QTableWidgetItem(vote_str)
            self.table_bb.setRowHeight(row_idx, 80)
            self.table_bb.setItem(row_idx, 1, vote_item)
            self.table_bb.setItem(row_idx, 2, QTableWidgetItem(row.get("commitment", "")))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = GUIApp()
    win.show()
    sys.exit(app.exec_())
