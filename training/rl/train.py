"""
Train a PPO agent to optimize RSI mean reversion strategy parameters.
Uses Stable-Baselines3.

Usage: python -m training.rl.train
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
    _sb3_available = True
except ImportError:
    _sb3_available = False

try:
    from .env import BacktestEnv
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from env import BacktestEnv


def train_agent(total_timesteps: int = 50000, symbol: str = "NIFTY",
                save_path: str = None):
    """
    Train PPO agent to optimize RSI strategy parameters.

    Args:
        total_timesteps: Number of training steps
        symbol: Market symbol to train on
        save_path: Path to save the model
    """
    if not _sb3_available:
        print("Stable-Baselines3 not installed. Install with: pip install stable-baselines3")
        print("Skipping RL training. The environment class is available for custom training.")
        return

    if save_path is None:
        save_path = os.path.join(os.path.dirname(__file__), "models", f"ppo_{symbol.lower()}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    def make_env():
        return BacktestEnv(symbol=symbol, period="5y")

    env = DummyVecEnv([make_env])

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        tensorboard_log=os.path.join(os.path.dirname(save_path), "logs"),
    )

    eval_env = DummyVecEnv([lambda: BacktestEnv(symbol=symbol, period="2y")])
    callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.dirname(save_path),
        log_path=os.path.join(os.path.dirname(save_path), "eval_logs"),
        eval_freq=5000,
        deterministic=True,
        render=False,
    )

    print(f"Training PPO agent on {symbol} for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps, callback=callback)
    model.save(save_path)
    print(f"Model saved to {save_path}")

    env.close()
    eval_env.close()
    return model


def evaluate_agent(model_path: str, symbol: str = "NIFTY", n_episodes: int = 10):
    """Evaluate a trained agent over multiple episodes."""
    if not _sb3_available:
        print("Stable-Baselines3 not installed.")
        return

    from stable_baselines3 import PPO
    model = PPO.load(model_path)
    env = BacktestEnv(symbol=symbol, period="2y")

    rewards = []
    sharpes = []

    for ep in range(n_episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            ep_reward += reward

        rewards.append(ep_reward)
        if "sharpe" in info:
            sharpes.append(info.get("sharpe", 0))

    print(f"Evaluation over {n_episodes} episodes:")
    print(f"  Average return: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
    if sharpes:
        print(f"  Avg Sharpe: {np.mean(sharpes):.3f}")
    print(f"  Max return: {np.max(rewards):.2f}")
    print(f"  Min return: {np.min(rewards):.2f}")

    env.close()


if __name__ == "__main__":
    train_agent(total_timesteps=50000, symbol="NIFTY")
