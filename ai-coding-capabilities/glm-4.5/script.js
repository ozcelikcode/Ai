class SudokuGame {
    constructor() {
        this.board = [];
        this.solution = [];
        this.initialBoard = [];
        this.selectedCell = null;
        this.difficulty = 'easy';
        this.variant = 'classic';
        this.mistakes = 0;
        this.maxMistakes = 3;
        this.score = 0;
        this.timer = 0;
        this.timerInterval = null;
        this.gameStarted = false;
        this.history = [];
        this.hints = 3;
        this.autoValidate = true; // Enable automatic validation
        
        this.initializeGame();
        this.setupEventListeners();
    }

    initializeGame() {
        this.createBoard();
        this.renderBoard();
        this.updateStats();
    }

    createBoard() {
        // Create empty 9x9 board
        this.board = Array(9).fill().map(() => Array(9).fill(0));
        this.solution = Array(9).fill().map(() => Array(9).fill(0));
        this.initialBoard = Array(9).fill().map(() => Array(9).fill(0));
        
        // Generate a complete valid Sudoku solution
        this.generateSolution();
        
        // Copy solution to board and remove numbers based on difficulty
        this.copySolutionToBoard();
        this.removeNumbers();
        
        // Store initial state
        this.initialBoard = this.board.map(row => [...row]);
    }

    generateSolution() {
        // Fill the board with a valid solution
        this.fillBoard(this.solution);
    }

    fillBoard(board) {
        const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9];
        
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (board[row][col] === 0) {
                    this.shuffleArray(numbers);
                    
                    for (let num of numbers) {
                        if (this.isValidMove(board, row, col, num)) {
                            board[row][col] = num;
                            
                            if (this.fillBoard(board)) {
                                return true;
                            }
                            
                            board[row][col] = 0;
                        }
                    }
                    return false;
                }
            }
        }
        return true;
    }

    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    isValidMove(board, row, col, num) {
        // Check row
        for (let x = 0; x < 9; x++) {
            if (board[row][x] === num) return false;
        }
        
        // Check column
        for (let x = 0; x < 9; x++) {
            if (board[x][col] === num) return false;
        }
        
        // Check 3x3 box
        const boxRow = Math.floor(row / 3) * 3;
        const boxCol = Math.floor(col / 3) * 3;
        
        for (let i = 0; i < 3; i++) {
            for (let j = 0; j < 3; j++) {
                if (board[boxRow + i][boxCol + j] === num) return false;
            }
        }
        
        // Check diagonal constraints for diagonal variant
        if (this.variant === 'diagonal') {
            // Main diagonal
            if (row === col) {
                for (let i = 0; i < 9; i++) {
                    if (board[i][i] === num) return false;
                }
            }
            
            // Anti-diagonal
            if (row + col === 8) {
                for (let i = 0; i < 9; i++) {
                    if (board[i][8 - i] === num) return false;
                }
            }
        }
        
        return true;
    }

    copySolutionToBoard() {
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                this.board[i][j] = this.solution[i][j];
            }
        }
    }

    removeNumbers() {
        const cellsToRemove = this.getCellsToRemove();
        const positions = [];
        
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                positions.push([i, j]);
            }
        }
        
        this.shuffleArray(positions);
        
        for (let i = 0; i < cellsToRemove && i < positions.length; i++) {
            const [row, col] = positions[i];
            this.board[row][col] = 0;
        }
    }

    getCellsToRemove() {
        const difficultyLevels = {
            easy: 35,
            medium: 45,
            hard: 55,
            expert: 65
        };
        
        return difficultyLevels[this.difficulty] || 35;
    }

    renderBoard() {
        const boardElement = document.getElementById('sudoku-board');
        boardElement.innerHTML = '';
        
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.row = row;
                cell.dataset.col = col;
                
                const value = this.board[row][col];
                if (value !== 0) {
                    cell.textContent = value;
                    
                    // Style system numbers differently
                    if (this.initialBoard[row][col] !== 0) {
                        cell.classList.add('fixed');
                        // Make system numbers more prominent
                        cell.style.fontWeight = '700';
                        cell.style.color = 'var(--text-primary)';
                        cell.style.backgroundColor = 'var(--background-color)';
                    } else {
                        // User-entered numbers
                        cell.style.fontWeight = '500';
                        
                        // Auto-validate if enabled
                        if (this.autoValidate && value === this.solution[row][col]) {
                            cell.classList.add('correct');
                        } else if (this.autoValidate && value !== this.solution[row][col]) {
                            cell.classList.add('error');
                        }
                    }
                }
                
                cell.addEventListener('click', () => this.selectCell(row, col));
                boardElement.appendChild(cell);
            }
        }
    }

    selectCell(row, col) {
        // Allow clicking on system numbers for highlighting
        // Clear previous selection
        document.querySelectorAll('.cell').forEach(cell => {
            cell.classList.remove('selected', 'highlight', 'same-number');
        });
        
        // Select new cell
        this.selectedCell = { row, col };
        const selectedElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        selectedElement.classList.add('selected');
        
        // Highlight same numbers
        const value = this.board[row][col];
        if (value !== 0) {
            document.querySelectorAll('.cell').forEach(cell => {
                const cellValue = parseInt(cell.textContent) || 0;
                if (cellValue === value) {
                    cell.classList.add('same-number');
                }
            });
        }
        
        // Highlight row, column, and box
        this.highlightRelatedCells(row, col);
    }

    highlightRelatedCells(row, col) {
        // Highlight row
        for (let c = 0; c < 9; c++) {
            const cell = document.querySelector(`[data-row="${row}"][data-col="${c}"]`);
            cell.classList.add('highlight');
        }
        
        // Highlight column
        for (let r = 0; r < 9; r++) {
            const cell = document.querySelector(`[data-row="${r}"][data-col="${col}"]`);
            cell.classList.add('highlight');
        }
        
        // Highlight 3x3 box
        const boxRow = Math.floor(row / 3) * 3;
        const boxCol = Math.floor(col / 3) * 3;
        
        for (let r = boxRow; r < boxRow + 3; r++) {
            for (let c = boxCol; c < boxCol + 3; c++) {
                const cell = document.querySelector(`[data-row="${r}"][data-col="${c}"]`);
                cell.classList.add('highlight');
            }
        }
    }

    placeNumber(number) {
        if (!this.selectedCell) return;
        
        const { row, col } = this.selectedCell;
        if (this.initialBoard[row][col] !== 0) return;
        
        // Save move to history
        this.saveMove(row, col, this.board[row][col]);
        
        // Place number
        this.board[row][col] = number;
        
        // Update cell
        const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        cell.textContent = number || '';
        cell.classList.remove('error', 'correct');
        
        // Check if move is valid
        if (number !== 0) {
            const isValid = this.isValidMove(this.getBoardForValidation(), row, col, number);
            
            if (!isValid) {
                cell.classList.add('error');
                this.mistakes++;
                this.updateStats();
                
                if (this.mistakes >= this.maxMistakes) {
                    this.gameOver();
                }
            } else {
                // Check if the number is correct according to solution
                if (number === this.solution[row][col]) {
                    cell.classList.add('correct');
                    // Update score
                    this.score += 10;
                    this.updateStats();
                    
                    // Check if puzzle is complete
                    if (this.isPuzzleComplete()) {
                        this.gameComplete();
                    }
                } else {
                    // Number is valid but not correct
                    this.score = Math.max(0, this.score - 5);
                    this.updateStats();
                }
            }
        }
        
        // Restart timer if game hasn't started
        if (!this.gameStarted) {
            this.startTimer();
            this.gameStarted = true;
        }
        
        // Auto-validate all cells if enabled
        if (this.autoValidate) {
            this.autoValidateBoard();
        }
    }

    getBoardForValidation() {
        // Create a copy of the board for validation
        const boardCopy = this.board.map(row => [...row]);
        
        // Fill in fixed numbers from solution for validation
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                if (boardCopy[i][j] === 0 && this.initialBoard[i][j] === 0) {
                    boardCopy[i][j] = this.solution[i][j];
                }
            }
        }
        
        return boardCopy;
    }

    saveMove(row, col, oldValue) {
        this.history.push({
            row,
            col,
            oldValue,
            newValue: this.board[row][col]
        });
        
        // Limit history size
        if (this.history.length > 50) {
            this.history.shift();
        }
    }

    autoValidateBoard() {
        // Clear all validation classes
        document.querySelectorAll('.cell').forEach(cell => {
            if (!cell.classList.contains('fixed')) {
                cell.classList.remove('correct', 'error');
            }
        });
        
        // Validate all non-empty cells
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                const value = this.board[row][col];
                if (value !== 0 && this.initialBoard[row][col] === 0) {
                    const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
                    
                    if (value === this.solution[row][col]) {
                        cell.classList.add('correct');
                    } else {
                        cell.classList.add('error');
                    }
                }
            }
        }
    }

    undoMove() {
        if (this.history.length === 0) return;
        
        const lastMove = this.history.pop();
        this.board[lastMove.row][lastMove.col] = lastMove.oldValue;
        
        // Update cell
        const cell = document.querySelector(`[data-row="${lastMove.row}"][data-col="${lastMove.col}"]`);
        cell.textContent = lastMove.oldValue || '';
        cell.classList.remove('error');
        
        this.updateStats();
    }

    clearCell() {
        if (!this.selectedCell) return;
        
        const { row, col } = this.selectedCell;
        if (this.initialBoard[row][col] !== 0) return;
        
        this.saveMove(row, col, this.board[row][col]);
        this.board[row][col] = 0;
        
        const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        cell.textContent = '';
        cell.classList.remove('error', 'correct');
        
        // Auto-validate all cells if enabled
        if (this.autoValidate) {
            this.autoValidateBoard();
        }
    }

    checkSolution() {
        let hasErrors = false;
        
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (this.board[row][col] !== 0 && this.board[row][col] !== this.solution[row][col]) {
                    const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
                    cell.classList.add('error');
                    hasErrors = true;
                }
            }
        }
        
        if (!hasErrors && this.isPuzzleComplete()) {
            this.gameComplete();
        } else if (!hasErrors) {
            this.showMessage("Henüz hata yok, devam edin!", "success");
        } else {
            this.showMessage("Bazı hatalarınız var, lütfen kontrol edin.", "error");
        }
    }

    getHint() {
        if (!this.selectedCell) {
            this.showMessage("Önce bir hücre seçin!", "warning");
            return;
        }
        
        if (this.hints <= 0) {
            this.showMessage("İpucu hakkınız kalmadı!", "error");
            return;
        }
        
        const { row, col } = this.selectedCell;
        if (this.initialBoard[row][col] !== 0) {
            this.showMessage("Bu hücre zaten dolu!", "warning");
            return;
        }
        
        if (this.board[row][col] === this.solution[row][col]) {
            this.showMessage("Bu hücre zaten doğru!", "success");
            return;
        }
        
        // Place correct number
        this.board[row][col] = this.solution[row][col];
        const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        cell.textContent = this.solution[row][col];
        cell.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
        
        this.hints--;
        this.score = Math.max(0, this.score - 20);
        this.updateStats();
        
        setTimeout(() => {
            cell.style.backgroundColor = '';
        }, 2000);
        
        if (this.isPuzzleComplete()) {
            this.gameComplete();
        }
    }

    isPuzzleComplete() {
        for (let row = 0; row < 9; row++) {
            for (let col = 0; col < 9; col++) {
                if (this.board[row][col] !== this.solution[row][col]) {
                    return false;
                }
            }
        }
        return true;
    }

    gameComplete() {
        this.stopTimer();
        const timeBonus = Math.max(0, 1000 - this.timer);
        this.score += timeBonus;
        this.updateStats();
        
        this.showMessage(`Tebrikler! Oyunu tamamladınız! Puan: ${this.score}`, "success");
        
        // Save to localStorage
        this.saveGameStats();
    }

    gameOver() {
        this.stopTimer();
        this.showMessage("Oyun bitti! Çok fazla haptınız var.", "error");
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            this.timer++;
            this.updateTimer();
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    updateTimer() {
        const minutes = Math.floor(this.timer / 60);
        const seconds = this.timer % 60;
        document.getElementById('timer').textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    updateStats() {
        document.getElementById('mistakes').textContent = `${this.mistakes}/${this.maxMistakes}`;
        document.getElementById('score').textContent = this.score;
        this.updateTimer();
    }

    showMessage(message, type) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }

    saveGameStats() {
        const stats = JSON.parse(localStorage.getItem('sudokuStats') || '{}');
        
        if (!stats[this.difficulty]) {
            stats[this.difficulty] = {
                bestScore: 0,
                gamesPlayed: 0,
                bestTime: null
            };
        }
        
        stats[this.difficulty].gamesPlayed++;
        stats[this.difficulty].bestScore = Math.max(stats[this.difficulty].bestScore, this.score);
        
        if (!stats[this.difficulty].bestTime || this.timer < stats[this.difficulty].bestTime) {
            stats[this.difficulty].bestTime = this.timer;
        }
        
        localStorage.setItem('sudokuStats', JSON.stringify(stats));
    }

    setupEventListeners() {
        // Number pad buttons
        document.querySelectorAll('.number-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const number = parseInt(btn.dataset.number);
                if (number === 0) {
                    this.clearCell();
                } else {
                    this.placeNumber(number);
                }
            });
        });
        
        // Keyboard input
        document.addEventListener('keydown', (e) => {
            if (!this.selectedCell) return;
            
            if (e.key >= '1' && e.key <= '9') {
                this.placeNumber(parseInt(e.key));
            } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
                this.clearCell();
            } else if (e.key === 'ArrowUp' && this.selectedCell.row > 0) {
                this.selectCell(this.selectedCell.row - 1, this.selectedCell.col);
            } else if (e.key === 'ArrowDown' && this.selectedCell.row < 8) {
                this.selectCell(this.selectedCell.row + 1, this.selectedCell.col);
            } else if (e.key === 'ArrowLeft' && this.selectedCell.col > 0) {
                this.selectCell(this.selectedCell.row, this.selectedCell.col - 1);
            } else if (e.key === 'ArrowRight' && this.selectedCell.col < 8) {
                this.selectCell(this.selectedCell.row, this.selectedCell.col + 1);
            } else if (e.key === 'z' && (e.ctrlKey || e.metaKey)) {
                this.undoMove();
            }
        });
        
        // Difficulty buttons
        document.querySelectorAll('.difficulty-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.difficulty-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.difficulty = btn.dataset.difficulty;
                this.newGame();
            });
        });
        
        // Variant buttons
        document.querySelectorAll('.variant-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.variant-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.variant = btn.dataset.variant;
                this.newGame();
            });
        });
    }

    newGame() {
        this.stopTimer();
        this.timer = 0;
        this.mistakes = 0;
        this.score = 0;
        this.gameStarted = false;
        this.history = [];
        this.hints = 3;
        
        this.createBoard();
        this.renderBoard();
        this.updateStats();
    }
}

// Global functions for HTML onclick events
let game;

function showNewGameModal() {
    document.getElementById('new-game-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function startNewGame() {
    const difficulty = document.querySelector('input[name="difficulty"]:checked').value;
    const variant = document.querySelector('input[name="variant"]:checked').value;
    
    game.difficulty = difficulty;
    game.variant = variant;
    
    game.newGame();
    closeModal('new-game-modal');
}

function showStats() {
    const stats = JSON.parse(localStorage.getItem('sudokuStats') || '{}');
    let statsMessage = 'İstatistikler:\n\n';
    
    for (const [difficulty, data] of Object.entries(stats)) {
        statsMessage += `${difficulty.toUpperCase()}: \n`;
        statsMessage += `  - Oyun Sayısı: ${data.gamesPlayed}\n`;
        statsMessage += `  - En Yüksek Puan: ${data.bestScore}\n`;
        if (data.bestTime) {
            const minutes = Math.floor(data.bestTime / 60);
            const seconds = data.bestTime % 60;
            statsMessage += `  - En İyi Zaman: ${minutes}:${seconds.toString().padStart(2, '0')}\n`;
        }
        statsMessage += '\n';
    }
    
    if (statsMessage === 'İstatistikler:\n\n') {
        statsMessage = 'Henüz oyun oynanmamış!';
    }
    
    game.showMessage(statsMessage, 'success');
}

function showHelp() {
    const helpMessage = `Sudoku Oyunu Yardım:

1. Oynanış:
   - Boş hücrelere 1-9 arası sayılar yerleştirin
   - Her satır, sütun ve 3x3 kutuda tüm sayılar bir kez bulunmalı
   - Fare ile hücre seçin ve sayı tuşlarına basın

2. Kontroller:
   - Sayı tuşları (1-9): Sayı yerleştirir
   - Backspace/Delete: Hücreyi temizler
   - Ok tuşları: Hücre seçimini hareket ettirir
   - Ctrl+Z: Son hamleyi geri alır

3. Özellikler:
   - Kontrol Et: Mevcut durumu kontrol eder
   - İpucu: Doğru sayıyı gösterir (-20 puan)
   - Temizle: Seçili hücreyi temizler
   - Geri Al: Son hamleyi geri alır

4. Sudoku Türleri:
   - Klasik: Standart Sudoku kuralları
   - Çapraz: Ek olarak çaprazlarda sayılar tekrarlanamaz
   - Killer: Sayıların toplamı belirli kurallara uyar
   - Samurai: 5 birleşik Sudoku tahtası

İyi oyunlar!`;
    
    game.showMessage(helpMessage, 'success');
}

function checkSolution() {
    game.checkSolution();
}

function getHint() {
    game.getHint();
}

function clearCell() {
    game.clearCell();
}

function undoMove() {
    game.undoMove();
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    game = new SudokuGame();
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
});