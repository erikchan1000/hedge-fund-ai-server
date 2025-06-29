# AI Hedge Fund

This project consists of a Python backend server and a Next.js frontend client for an AI-powered hedge fund system.

## Project Structure

- `server/` - Python backend server
- `client/` - Next.js frontend application

## Server Setup

1. Navigate to the server directory:
```bash
cd server
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the server directory with the following variables:
```env
OPENAI_API_KEY=your_openai_api_key
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_api_secret
POLYGON_API_KEY=your_polygon_api_key <- recommended
```

4. Start the server:
- On Windows:
```bash
.\start.bat
```
- On macOS/Linux:
```bash
./start.sh
```

## Client Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
yarn
```

3. Start the development server:
```bash
yarn dev
```

The client will be available at `http://localhost:3000`

## Environment Variables

### Server (.env)
Required environment variables for the server:
- `OPENAI_API_KEY`: Your OpenAI API key
- `ALPACA_API_KEY`: Your Alpaca API key
- `ALPACA_API_SECRET`: Your Alpaca API secret

## Development

- Server runs on `http://localhost:5000` by default
- Client runs on `http://localhost:3000` by default

## Demo
![image](https://github.com/user-attachments/assets/c5fdaf4c-d650-4c17-b2c1-c3720e32a847)
![image](https://github.com/user-attachments/assets/80bd0fa6-cfda-4f3d-b2a8-ef66a0eddc68)

