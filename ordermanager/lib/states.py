#class SAStateMachine(object):
#    def __init__(self, sa_column


#states = (u"Заявка свободна", u"Заявка выполняется", u"Заявка ожидает", u"Заявка отмечена выполненной", u"Выполнение подтверждено")
#init_state = 0
#final_states = [5]
#transitions = [(0,1,takeCond),(]

#class OrderStateMachine(StateMachine):
new = State(1, u"Заявка свободна")
performing = State(2, u"Заявка выполняется")
waiting = State(3, u"Заявка ожидает")
markdone = State(4, u"Заявка отмечена выполненной")
done = State(5, u"Выполнение подтверждено")

states = [new, performing, waiting, markdone, done]
init_state = new
final_states = [done]

transitions = [
    ((u"Взять заявку себе", u"Заявка взята"), new, performing, takeCond),
    ((u"Изменить исполнителей", u"Исполнители изменены"), performing, performing, changePerfsCond),
    ((u"Отметить выполненной", u"Отмечена выполненной"), performing, markdone, markDoneCond),
    ((u"Подтвердить выполнение", u"Выполнение подтвержено"), markdone, done, doneCond),
            
]
