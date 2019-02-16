from src.domain.model_couple import exploration, satisfaction


def test_simple_couples():
    persons = ['Em',
               'Pop',
               'E',
               'Palpal',
               ]
    dispos_per_persons = {'Em': [[1,4],[4,8],[12, 16]],
                          'Pop': [[1,4],[12,16],[16, 20]],
                          'E': [[4,8],[12,16],[16, 20]],
                          'Palpal': [[12,16],[16, 20]],
                          }


    print('---- Exploration ----')
    exploration_status, exploration_assignments, maximisation = exploration(persons, dispos_per_persons)

    print('---- Satisfaction ----')
    satisfaction_status, satisfaction_assignments = satisfaction(persons, dispos_per_persons, maximisation)