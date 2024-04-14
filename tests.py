import datetime
import unittest
import database

from sqlmodel import Session, SQLModel, create_engine, select, update


engine = create_engine("sqlite:///test_database.db")



SQLModel.metadata.create_all(engine)

import app

class Tests(unittest.TestCase):
    def test_decay(self):
        with Session(engine) as session:
            session.add(database.AltData(altitude=159, last_updated=datetime.datetime.now() - datetime.timedelta(seconds=59)))
            session.commit()
            assert app.health_logic() == "WARNING: RAPID ORBITAL DECAY IMMINENT"

            assert session.exec(select(database.AltHealthData)).one()

    def test_decay_then_recover(self):
        with Session(engine) as session:
            assert session.exec(select(database.AltHealthData)).one()
            session.add(database.AltData(altitude=180, last_updated=datetime.datetime.now() - datetime.timedelta(seconds=59)))
            session.add(database.AltData(altitude=200, last_updated=datetime.datetime.now() - datetime.timedelta(seconds=59)))
            session.commit()
            assert app.health_logic() == "Sustained Low Earth Orbit Resumed"
            # fake forward time motion (could be done with a library in a less hacky way) so that we are outside of the 1 minute time frame
            session.exec(update(database.AltHealthData).where(database.AltHealthData.orbit_sustained_timestamp != None).values(orbital_decay_timestamp =datetime.datetime.now()-datetime.timedelta(minutes=2)))
            # then adding a new good altitude in the current timeframe to keep us in the happy path
            session.add(database.AltData(altitude=200, last_updated=datetime.datetime.now() - datetime.timedelta(seconds=30)))
            session.commit()
            
            assert app.health_logic() == "Altitude is A-OK"

            assert session.exec(select(database.AltHealthData)).one()
        
    @classmethod
    def tearDownClass(cls) -> None:
        SQLModel.metadata.drop_all(engine)
        return super().tearDownClass()

if __name__ == "__main__":
    unittest.main()
