import json
from django.db import models

class JobAlreadyFinishedException(Exception):
    pass

class Actions:
    def end_job():
        return 'END_JOB'

    def go_to_step(step):
        return ' '.join(['GO_TO_STEP', str(step)])

class Workflow(models.Model):
    name = models.CharField(max_length=255, default='abc123')
    execution_order = models.JSONField(default=dict)

    def set_steps(self, steps):
        execution_order = steps
        for key in execution_order.keys():
            step = execution_order[key]['step']
            step.workflow = self
            execution_order[key].pop('step')
            execution_order[key].update({'step_id': step.id})
        self.execution_order = json.dumps(execution_order)
        self.save()

class Step(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps', blank=True)
    name = models.CharField(max_length=255)
    return_value = models.IntegerField(default=None, null=True)

class States(models.TextChoices):
    NOT_STARTED = 'NS', 'Not Started'
    STARTED = 'S', 'Started'
    FINISHED = 'F', 'FINISHED'

class Job(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='jobs')
    current_execution_step = models.IntegerField(default=None, blank=True, null=True)
    state = models.CharField(max_length=2, choices=States.choices, default=States.NOT_STARTED)
    data = models.JSONField(default=dict)

    @property
    def current_step(self):
        execution_order = json.loads(self.workflow.execution_order)
        step_id = execution_order[self.current_execution_step]['step_id']
        return self.workflow.steps.get(id=step_id)

    def start(self):
        self.state = States.STARTED
        self.current_execution_step = '0'
        self.save()
        return self.current_step

    def get_data_for_step(self, step):
        data = json.loads(self.data)[str(step)]
        return data

    def set_data_for_step(self, step, data):
        old_data = self.data
        old_data.update({str(step): data})
        self.data = json.dumps(old_data)
        self.save()

    def accept_step(self):
        if self.state == States.FINISHED:
            raise JobAlreadyFinishedException
        execution_order = json.loads(self.workflow.execution_order)
        action = execution_order[self.current_execution_step]['accept']
        action_parsed = action.split(' ')

        if len(action_parsed) > 1:
            command, arguments = action_parsed[0], action_parsed[1:]
            if command == 'GO_TO_STEP' and self.state != States.FINISHED:
                self.current_execution_step = arguments[0]
        elif action_parsed[0] == 'END_JOB' and self.state != States.FINISHED:
            self.state = States.FINISHED
            self.current_execution_step = None

        self.save()
