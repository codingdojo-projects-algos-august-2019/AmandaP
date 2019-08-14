from config import app
import routes
from models.user_models import User
from models.event_models import Event, EventAttendance
from models.dog_models import Dog, DogSize


if __name__ == "__main__":
    app.run(debug=False)
