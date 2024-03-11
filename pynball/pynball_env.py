import random
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from pynball.point import Point
from pynball.ball import Ball
from pynball.polygon_obstacle import PolygonObstacle
from pynball.target import Target

ACTION_DICT = {
    0: (1.0, 0.0),
    1: (0.0, 1.0),
    2: (-1.0, 0.0),
    3: (0.0, -1.0),
    4: (0.0, 0.0),
}
# ACC_X, ACC_Y, DEC_X, DEC_Y, NOP

THRUST_PENALTY = -5.0
NOP_PENALTY = -1.0


class PynBall:
    """A Pinball game domain.

    Attributes:
        config (dict): Configuration parameters.
        step_duration (int): The number of inner-steps per step.
        drag (float): Drag factor applied to ball each step.
        obstacles (list[PolygonObstacle]): Obstacles in the environment.
        target (Target): Target instance of the environment.
        ball (Ball): The ball that travels in the environment.
        reset_flag (bool): Tracks whether the environment has been reset.
    """

    def __init__(
        self,
        config_path: str | None = None,
    ) -> None:

        config_path = Path(config_path)
        with open(config_path, "rb") as fb:
            self.config = tomllib.load(fb)

        random.seed(self.config["seed"])
        self.step_duration: int = self.config["step_duration"]
        self.drag: float = self.config["drag"]
        self.obstacles = [
            PolygonObstacle([Point(*point) for point in obstacle["points"]])
            for obstacle in self.config["obstacles"]
        ]

        self.target = Target(
            Point(*self.config["target"]["location"]), self.config["target"]["radius"]
        )

        self.reset_flag: bool = False
        self.ball: Ball | None = None

    def reset(self, starting_ball: Ball | None = None) -> tuple:
        """Resets the environment.

        An optional argument allows a Ball object to be provided.
        Otherwise, a ball with zero velocity is created at one of the
        start locations in the config file.

        Args:
            starting_ball (Ball | None, optional): Ball to reset the
            environment with. Defaults to None.

        Returns:
            tuple: Current state as (ball.x, ball.y, ball.xdot, ball.ydot).
        """
        if starting_ball is None:
            self.ball = Ball(
                p=Point(*random.choice(self.config["ball"]["starts"])),
                radius=self.config["ball"]["radius"],
            )
        else:
            self.ball = starting_ball
        self.reset_flag = True
        return (self.ball.x, self.ball.y, self.ball.xdot, self.ball.ydot)

    def terminal(self) -> bool:
        """Checks if the the environment is in a terminal state.

        State is terminal if the ball has collided with the environment.

        Returns:
            bool: True if the state is terminal, False otherwise.
        """
        return self.target.collision(self.ball)

    def step(self, action: int) -> tuple:
        """Advances the environment one timestep.

        Each timestep is divided into `self.step_duration` inner steps.
        Each inner step, all obstacles are checked for collision and the
        velocity updated accordingly.
        Drag is added after all inner steps are complete.

        Args:
            action (int): Action to take. Used as key for ACTION_DICT:
            0: ACC_X, 1: ACC_Y, 2: DEC_X, 3: DEC_Y, 4: NOP

        Returns:
            tuple: (state, reward, terminal, info)
        """
        assert self.reset_flag is True, "Environment requires resetting."
        x_impulse, y_impulse = ACTION_DICT[action]
        reward = NOP_PENALTY if action == 4 else THRUST_PENALTY
        terminal = False
        self.ball.add_impulse(x_impulse, y_impulse)
        for i in range(self.step_duration):
            num_collisions = 0
            collidor: PolygonObstacle = None
            self.ball.step(self.step_duration)

            for obstacle in self.obstacles:
                if obstacle.collision(self.ball):
                    num_collisions += 1
                    collidor = obstacle

            if num_collisions == 1:
                new_vel = collidor.collision_effect(self.ball)
                self.ball.set_velocity(new_vel)
                if i == self.step_duration - 1:
                    # Add a bonus step to ensure ball bounces away from obstacle.
                    self.ball.step()
            elif num_collisions > 1:
                # If there are multiple collisions, reverse velocity.
                new_vel = Point(-self.ball.xdot, -self.ball.ydot)
                self.ball.set_velocity(new_vel)

            if self.terminal():
                terminal = True
                self.reset_flag = False
                break

        self.ball.add_drag(self.drag)
        self.check_bounds()
        current_state = (self.ball.x, self.ball.y, self.ball.xdot, self.ball.ydot)
        return current_state, reward, terminal, None

    def check_bounds(self) -> None:
        """Checks that the ball is within the bounds of the game area.

        Raises:
            RuntimeError: Ball out of bounds error.
        """
        point = self.ball.get_center()
        if not (0.0 < point.x < 1.0 and 0.0 < point.y < 1.0):
            raise RuntimeError("Ball out of bounds")

    def render(self):
        """Renders the current state of an environment.

        Args:
            env (PynBall): The environment to render.
        """
        _, ax = plt.subplots()
        for obstacle in self.obstacles:
            points = [(p.x, p.y) for p in obstacle.points]
            ax.add_patch(Polygon(points, facecolor="k"))
        ax.add_patch(
            Circle(
                [self.target.point.x, self.target.point.y],
                self.target.radius,
                facecolor="r",
            )
        )
        ax.add_patch(
            Circle([self.ball.x, self.ball.y], self.ball.radius, facecolor="b")
        )
        r = self.ball.radius
        ax.arrow(
            self.ball.x,
            self.ball.y,
            self.ball.xdot * 2 * r,
            self.ball.ydot * 2 * r,
            head_width=0.03,
            head_length=0.03,
            facecolor="g",
            edgecolor="g",
        )
        plt.show()
        # plt.draw()
        # plt.pause(0.1)
