const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const scoreDisplay = document.getElementById('score');
const highScoreDisplay = document.getElementById('high-score');
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const restartBtn = document.getElementById('restart-btn');

const gridSize = 20;
const tileCount = canvas.width / gridSize;

let snake = [{x: 10, y: 10}];
let food = {x: 15, y: 15};
let dx = 0;
let dy = 0;
let score = 0;
let highScore = localStorage.getItem('snakeHighScore') || 0;
highScoreDisplay.textContent = highScore;
let gameRunning = false;
let gameLoop;

function drawGame() {
    clearCanvas();
    drawFood();
    drawSnake();
}

function clearCanvas() {
    ctx.fillStyle = 'black';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawSnake() {
    ctx.fillStyle = 'lime';
    snake.forEach(segment => {
        ctx.fillRect(segment.x * gridSize, segment.y * gridSize, gridSize - 2, gridSize - 2);
    });
}

function drawFood() {
    ctx.fillStyle = 'red';
    ctx.fillRect(food.x * gridSize, food.y * gridSize, gridSize - 2, gridSize - 2);
}

function moveSnake() {
    const head = {x: snake[0].x + dx, y: snake[0].y + dy};
    snake.unshift(head);
    if (head.x === food.x && head.y === food.y) {
        score += 10;
        scoreDisplay.textContent = score;
        if (score > highScore) {
            highScore = score;
            highScoreDisplay.textContent = highScore;
            localStorage.setItem('snakeHighScore', highScore);
        }
        generateFood();
    } else {
        snake.pop();
    }
}

function generateFood() {
    food.x = Math.floor(Math.random() * tileCount);
    food.y = Math.floor(Math.random() * tileCount);
    snake.forEach(segment => {
        if (segment.x === food.x && segment.y === food.y) {
            generateFood();
        }
    });
}

function checkCollision() {
    const head = snake[0];
    if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
        return true;
    }
    for (let i = 1; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            return true;
        }
    }
    return false;
}

function gameStep() {
    if (!gameRunning) return;
    moveSnake();
    if (checkCollision()) {
        gameOver();
        return;
    }
    drawGame();
}

function startGame() {
    if (gameRunning) return;
    gameRunning = true;
    gameLoop = setInterval(gameStep, 100);
}

function pauseGame() {
    gameRunning = !gameRunning;
    if (gameRunning) {
        gameLoop = setInterval(gameStep, 100);
    } else {
        clearInterval(gameLoop);
    }
}

function restartGame() {
    clearInterval(gameLoop);
    snake = [{x: 10, y: 10}];
    food = {x: 15, y: 15};
    dx = 0;
    dy = 0;
    score = 0;
    scoreDisplay.textContent = score;
    gameRunning = false;
    drawGame();
}

function gameOver() {
    gameRunning = false;
    clearInterval(gameLoop);
    alert('Game Over! Score: ' + score);
}

function changeDirection(event) {
    const keyPressed = event.key;
    const goingUp = dy === -1;
    const goingDown = dy === 1;
    const goingRight = dx === 1;
    const goingLeft = dx === -1;

    if ((keyPressed === 'ArrowUp' || keyPressed === 'w') && !goingDown) {
        dx = 0;
        dy = -1;
    } else if ((keyPressed === 'ArrowDown' || keyPressed === 's') && !goingUp) {
        dx = 0;
        dy = 1;
    } else if ((keyPressed === 'ArrowLeft' || keyPressed === 'a') && !goingRight) {
        dx = -1;
        dy = 0;
    } else if ((keyPressed === 'ArrowRight' || keyPressed === 'd') && !goingLeft) {
        dx = 1;
        dy = 0;
    }
}

startBtn.addEventListener('click', startGame);
pauseBtn.addEventListener('click', pauseGame);
restartBtn.addEventListener('click', restartGame);
document.addEventListener('keydown', changeDirection);

drawGame();