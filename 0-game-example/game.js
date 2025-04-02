// Game constants
const GAME_WIDTH = 800;
const GAME_HEIGHT = 500;
const ROAD_LANES = 3; // Reduced to have fewer but more distinct lanes
const LANE_HEIGHT = 60; // Fixed lane height
const GRASS_HEIGHT = 80; // Height of grass areas
const CHICKEN_WIDTH = 40;
const CHICKEN_HEIGHT = 40;
const CAR_WIDTH = 80;
const CAR_HEIGHT = 40;
const CAR_SPEED_MIN = 2;
const CAR_SPEED_MAX = 5;
const CHICKEN_SPEED = 4;
const INITIAL_EGGS = 3;

// Game state
let score = 0;
let eggsRemaining = INITIAL_EGGS;
let isGameRunning = false;
let chicken = null;
let cars = [];
let roadSections = []; // Store road sections
let grassSections = []; // Store grass sections
let trees = []; // Store trees
let gameLoop = null;
let lastCarSpawn = 0;
let carSpawnRate = 60; // frames between car spawns
let keyState = {};

// Initialize PixiJS
const app = new PIXI.Application({
  width: GAME_WIDTH,
  height: GAME_HEIGHT,
  backgroundColor: 0x87ceeb, // Sky blue background
  antialias: true,
});

// Create the environment (roads and grass)
function createEnvironment() {
  // Calculate position of each lane and grass section
  const totalSections = ROAD_LANES * 2 - 1; // Alternating road and grass
  let currentY = 40; // Start a bit from the top

  // Create sections from top to bottom
  for (let i = 0; i < totalSections; i++) {
    if (i % 2 === 0) {
      // Road section
      createRoadSection(currentY, i / 2);
      currentY += LANE_HEIGHT;
    } else {
      // Grass section
      createGrassSection(currentY);
      currentY += GRASS_HEIGHT;

      // Add some trees to grass section
      addTreesToGrassSection(currentY - GRASS_HEIGHT / 2);
    }
  }

  // Add grass at the very bottom and top
  createGrassSection(0, 30);
  createGrassSection(currentY, GAME_HEIGHT - currentY);

  // Add trees to top and bottom grass areas
  addTreesToGrassSection(15);
  addTreesToGrassSection(GAME_HEIGHT - 30);
}

// Create a road section
function createRoadSection(y, laneIndex) {
  const roadSection = new PIXI.Graphics();

  // Road background
  roadSection.beginFill(0x808080); // Gray road
  roadSection.drawRect(0, y, GAME_WIDTH, LANE_HEIGHT);
  roadSection.endFill();

  // Road markings (white dashed lines)
  roadSection.beginFill(0xffffff);
  for (let x = 0; x < GAME_WIDTH; x += 50) {
    roadSection.drawRect(x, y + LANE_HEIGHT / 2 - 2, 20, 4);
  }
  roadSection.endFill();

  app.stage.addChild(roadSection);
  roadSections.push({
    sprite: roadSection,
    y: y,
    laneIndex: laneIndex,
  });
}

// Create a grass section
function createGrassSection(y, height = GRASS_HEIGHT) {
  const grassSection = new PIXI.Graphics();

  // Grass background
  grassSection.beginFill(0x7cfc00); // Bright green grass
  grassSection.drawRect(0, y, GAME_WIDTH, height);
  grassSection.endFill();

  app.stage.addChild(grassSection);
  grassSections.push({
    sprite: grassSection,
    y: y,
  });
}

// Add trees to a grass section
function addTreesToGrassSection(centerY) {
  // Add 3-5 trees randomly along the width
  const numTrees = Math.floor(Math.random() * 3) + 3;

  for (let i = 0; i < numTrees; i++) {
    // Calculate random x position, but ensure trees aren't too close to edges
    const x = Math.random() * (GAME_WIDTH - 100) + 50;
    createTree(x, centerY);
  }
}

// Create a tree
function createTree(x, y) {
  const treeContainer = new PIXI.Container();

  // Tree trunk
  const trunk = new PIXI.Graphics();
  trunk.beginFill(0x8b4513); // Brown
  trunk.drawRect(-5, 0, 10, 20);
  trunk.endFill();

  // Tree top (leaves)
  const leaves = new PIXI.Graphics();
  leaves.beginFill(0x2e8b57); // Dark green
  leaves.drawCircle(0, -15, 20);
  leaves.endFill();

  treeContainer.addChild(trunk);
  treeContainer.addChild(leaves);

  // Position the tree
  treeContainer.x = x;
  treeContainer.y = y;

  app.stage.addChild(treeContainer);
  trees.push(treeContainer);
}

// Create the chicken
function createChicken() {
  const chickenContainer = new PIXI.Container();

  // Chicken body (white)
  const body = new PIXI.Graphics();
  body.beginFill(0xffffff); // White
  body.drawEllipse(0, 0, CHICKEN_WIDTH / 2, CHICKEN_HEIGHT / 2);
  body.endFill();

  // Chicken eyes
  const eye = new PIXI.Graphics();
  eye.beginFill(0x000000); // Black
  eye.drawCircle(CHICKEN_WIDTH / 4, -CHICKEN_HEIGHT / 6, 3);
  eye.endFill();

  // Chicken beak
  const beak = new PIXI.Graphics();
  beak.beginFill(0xffa500); // Orange
  beak.drawPolygon([
    CHICKEN_WIDTH / 2,
    0,
    CHICKEN_WIDTH / 2 + 10,
    -5,
    CHICKEN_WIDTH / 2 + 10,
    5,
  ]);
  beak.endFill();

  // Chicken comb (red)
  const comb = new PIXI.Graphics();
  comb.beginFill(0xff0000); // Red
  comb.drawPolygon([
    0,
    -CHICKEN_HEIGHT / 2,
    -5,
    -CHICKEN_HEIGHT / 2 - 10,
    5,
    -CHICKEN_HEIGHT / 2 - 8,
    10,
    -CHICKEN_HEIGHT / 2 - 12,
    15,
    -CHICKEN_HEIGHT / 2 - 7,
  ]);
  comb.endFill();

  // Chicken legs
  const legs = new PIXI.Graphics();
  legs.beginFill(0xffa500); // Orange
  legs.drawRect(-CHICKEN_WIDTH / 4, CHICKEN_HEIGHT / 2, 3, 10);
  legs.drawRect(CHICKEN_WIDTH / 4, CHICKEN_HEIGHT / 2, 3, 10);
  legs.endFill();

  chickenContainer.addChild(body);
  chickenContainer.addChild(eye);
  chickenContainer.addChild(beak);
  chickenContainer.addChild(comb);
  chickenContainer.addChild(legs);

  // Add to the scene
  app.stage.addChild(chickenContainer);

  // Create chicken object
  chicken = {
    sprite: chickenContainer,
    x: GAME_WIDTH / 2,
    y: GAME_HEIGHT - 50,
    width: CHICKEN_WIDTH,
    height: CHICKEN_HEIGHT,
    reachedTop: false,
  };

  // Position the chicken
  chicken.sprite.x = chicken.x;
  chicken.sprite.y = chicken.y;

  return chicken;
}

// Create a car
function createCar(laneIndex) {
  const carContainer = new PIXI.Container();

  // Determine direction based on lane index
  const direction = laneIndex % 2 === 0 ? 1 : -1;

  // Car colors - more vibrant colors for vehicles
  const carColors = [0xff0000, 0x0000ff, 0x00ff00, 0xffffff];
  const carColor = carColors[Math.floor(Math.random() * carColors.length)];

  // Car type (0 = car, 1 = truck)
  const carType = Math.random() > 0.7 ? 1 : 0;
  let carWidth = carType === 0 ? CAR_WIDTH : CAR_WIDTH * 1.5;

  // Car body
  const body = new PIXI.Graphics();
  body.beginFill(carColor);

  if (carType === 0) {
    // Regular car
    body.drawRect(0, 0, carWidth, CAR_HEIGHT);
  } else {
    // Truck
    body.drawRect(0, 0, carWidth, CAR_HEIGHT);
  }
  body.endFill();

  // Car windows
  const windows = new PIXI.Graphics();
  windows.beginFill(0x87ceeb); // Light blue

  if (carType === 0) {
    // Car windows
    windows.drawRect(carWidth * 0.15, 5, carWidth * 0.3, CAR_HEIGHT - 10);
    windows.drawRect(carWidth * 0.6, 5, carWidth * 0.25, CAR_HEIGHT - 10);
  } else {
    // Truck windows
    windows.drawRect(carWidth * 0.8, 5, carWidth * 0.15, CAR_HEIGHT - 10);
  }
  windows.endFill();

  // Car wheels
  const wheels = new PIXI.Graphics();
  wheels.beginFill(0x000000); // Black

  // Front and back wheels
  wheels.drawCircle(carWidth * 0.2, CAR_HEIGHT, 5);
  wheels.drawCircle(carWidth * 0.8, CAR_HEIGHT, 5);

  if (carType === 1) {
    // Middle wheel for trucks
    wheels.drawCircle(carWidth * 0.5, CAR_HEIGHT, 5);
  }

  wheels.endFill();

  // Add all parts to the container
  carContainer.addChild(body);
  carContainer.addChild(windows);
  carContainer.addChild(wheels);

  // Flip car if moving right to left
  if (direction < 0) {
    carContainer.scale.x = -1;
    carContainer.x = carWidth; // Adjust for flipping
  }

  // Add to stage
  app.stage.addChild(carContainer);

  // Calculate the road's Y position for this lane
  const roadY = roadSections[laneIndex].y;
  const carY = roadY + (LANE_HEIGHT - CAR_HEIGHT) / 2;

  // Create the car object
  const car = {
    sprite: carContainer,
    x: direction > 0 ? -carWidth : GAME_WIDTH,
    y: carY,
    width: carWidth,
    height: CAR_HEIGHT,
    speed:
      (Math.random() * (CAR_SPEED_MAX - CAR_SPEED_MIN) + CAR_SPEED_MIN) *
      direction,
    laneIndex: laneIndex,
  };

  // Set initial position
  car.sprite.x = car.x;
  car.sprite.y = car.y;

  cars.push(car);
  return car;
}

// Initialize game
function initGame() {
  document.getElementById("game-canvas").appendChild(app.view);

  createEnvironment();
  chicken = createChicken();

  updateUI();
  setupEventListeners();
}

// Update UI elements
function updateUI() {
  document.getElementById("eggs-remaining").textContent = eggsRemaining;
  document.getElementById("score").textContent = score;
}

// Set game status message
function setGameStatus(message) {
  document.getElementById("game-status").textContent = message;
}

// Check collision between chicken and car
function checkCollision(chicken, car) {
  // Use a smaller hit area for more forgiving gameplay
  const chickenHitbox = {
    x: chicken.x - chicken.width * 0.3,
    y: chicken.y - chicken.height * 0.3,
    width: chicken.width * 0.6,
    height: chicken.height * 0.6,
  };

  return (
    chickenHitbox.x < car.x + car.width &&
    chickenHitbox.x + chickenHitbox.width > car.x &&
    chickenHitbox.y < car.y + car.height &&
    chickenHitbox.y + chickenHitbox.height > car.y
  );
}

// Handle collision with car
function handleCollision() {
  eggsRemaining--;
  updateUI();

  // Flash the chicken red
  chicken.sprite.tint = 0xff0000;

  setTimeout(() => {
    if (chicken) {
      chicken.sprite.tint = 0xffffff;
    }
  }, 500);

  // Reset chicken position
  chicken.x = GAME_WIDTH / 2;
  chicken.y = GAME_HEIGHT - 50;
  chicken.sprite.x = chicken.x;
  chicken.sprite.y = chicken.y;
  chicken.reachedTop = false;

  if (eggsRemaining <= 0) {
    endGame("Game Over! You lost all your eggs!");
  } else {
    setGameStatus(`Ouch! ${eggsRemaining} eggs remaining!`);
  }
}

// Main game update loop
function update() {
  // Move the chicken based on keyboard input
  if (keyState["ArrowLeft"] && chicken.x > 0) {
    chicken.x -= CHICKEN_SPEED;
  }
  if (keyState["ArrowRight"] && chicken.x < GAME_WIDTH - chicken.width) {
    chicken.x += CHICKEN_SPEED;
  }
  if (keyState["ArrowUp"] && chicken.y > 0) {
    chicken.y -= CHICKEN_SPEED;
  }
  if (keyState["ArrowDown"] && chicken.y < GAME_HEIGHT - chicken.height) {
    chicken.y += CHICKEN_SPEED;
  }

  // Update chicken sprite position
  chicken.sprite.x = chicken.x;
  chicken.sprite.y = chicken.y;

  // Check if chicken reached the top
  if (chicken.y <= 40 && !chicken.reachedTop) {
    // Chicken made it across!
    score++;
    updateUI();

    // Reset chicken position
    chicken.x = GAME_WIDTH / 2;
    chicken.y = GAME_HEIGHT - 50;
    chicken.sprite.x = chicken.x;
    chicken.sprite.y = chicken.y;
    chicken.reachedTop = true;

    setGameStatus(`Great! Score: ${score}`);

    // Increase difficulty
    if (score % 5 === 0 && carSpawnRate > 20) {
      carSpawnRate -= 5;
    }
  }

  // Spawn new cars
  lastCarSpawn++;
  if (lastCarSpawn >= carSpawnRate) {
    // Choose a random lane
    const laneIndex = Math.floor(Math.random() * ROAD_LANES);
    createCar(laneIndex);
    lastCarSpawn = 0;
  }

  // Update car positions
  for (let i = cars.length - 1; i >= 0; i--) {
    const car = cars[i];
    car.x += car.speed;

    if (car.speed < 0) {
      // If car is moving right to left, we need to adjust the sprite position
      // because of the flipped sprite
      car.sprite.x = car.x + car.width;
    } else {
      car.sprite.x = car.x;
    }

    // Check if car is out of bounds
    if (
      (car.speed > 0 && car.x > GAME_WIDTH) ||
      (car.speed < 0 && car.x + car.width < 0)
    ) {
      app.stage.removeChild(car.sprite);
      cars.splice(i, 1);
      continue;
    }

    // Check collision with chicken
    if (checkCollision(chicken, car)) {
      handleCollision();
    }
  }
}

// Start the game
function startGame() {
  if (isGameRunning) return;

  isGameRunning = true;
  setGameStatus("Go! Cross the road!");

  // Start the game loop
  app.ticker.add(update);

  // Enable start button again once game is running
  document.getElementById("start-btn").textContent = "Pause";
}

// Pause the game
function pauseGame() {
  if (!isGameRunning) return;

  isGameRunning = false;
  setGameStatus("Game Paused");

  // Stop the game loop
  app.ticker.remove(update);

  // Update button text
  document.getElementById("start-btn").textContent = "Resume";
}

// End the game
function endGame(message) {
  isGameRunning = false;
  setGameStatus(message || "Game Over!");

  // Stop the game loop
  app.ticker.remove(update);

  // Update button text
  document.getElementById("start-btn").textContent = "Play Again";
}

// Reset the game
function resetGame() {
  // Stop the current game if running
  if (isGameRunning) {
    app.ticker.remove(update);
  }

  // Reset game state
  score = 0;
  eggsRemaining = INITIAL_EGGS;
  isGameRunning = false;
  lastCarSpawn = 0;
  carSpawnRate = 60;

  // Clear all cars
  for (const car of cars) {
    app.stage.removeChild(car.sprite);
  }
  cars = [];

  // Reset chicken position
  if (chicken) {
    chicken.x = GAME_WIDTH / 2;
    chicken.y = GAME_HEIGHT - 50;
    chicken.sprite.x = chicken.x;
    chicken.sprite.y = chicken.y;
    chicken.reachedTop = false;
    chicken.sprite.tint = 0xffffff; // Reset tint
  }

  // Update UI
  updateUI();
  setGameStatus("Get ready!");
  document.getElementById("start-btn").textContent = "Start Game";
}

// Helper function to draw a triangle
PIXI.Graphics.prototype.drawTriangle = function (x1, y1, x2, y2, x3, y3) {
  this.moveTo(x1, y1);
  this.lineTo(x2, y2);
  this.lineTo(x3, y3);
  this.lineTo(x1, y1);
  return this;
};

// Event listeners
function setupEventListeners() {
  // Keyboard event listeners
  document.addEventListener("keydown", (e) => {
    keyState[e.key] = true;

    // Prevent default action for arrow keys (scrolling the page)
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
      e.preventDefault();
    }
  });

  document.addEventListener("keyup", (e) => {
    keyState[e.key] = false;
  });

  // Button event listeners
  document.getElementById("start-btn").addEventListener("click", () => {
    if (isGameRunning) {
      pauseGame();
    } else {
      if (eggsRemaining <= 0) {
        resetGame();
      }
      startGame();
    }
  });

  document.getElementById("reset-btn").addEventListener("click", resetGame);
}

// Start the game
initGame();
