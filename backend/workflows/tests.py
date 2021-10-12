from django.test import TestCase
from workflows.models import Workflow, Step, Job, Actions, JobAlreadyFinishedException
import django

class WorkflowsModelsTestCase(TestCase):
    def setUp(self):
        pass

    def test_workflow_blueprints_know_their_steps_in_order(self):
        wf = Workflow()
        wf.save()
        step1 = Step(workflow=wf)
        step1.save()
        step2 = Step(workflow=wf)
        step2.save()
        wf.set_steps({
            0: {'step': step1, 'accept': Actions.go_to_step(1), 'reject': Actions.end_job()},
            1: {'step': step2, 'accept': Actions.end_job()},
        })

        self.assertEqual(wf.steps.all()[0], step1)
        self.assertEqual(wf.steps.all()[1], step2)

    def test_workflow_steps_execute_in_correct_order(self):
        wf = Workflow()
        wf.save()
        step1 = Step(workflow=wf)
        step1.save()
        step2 = Step(workflow=wf)
        step2.save()
        step3 = Step(workflow=wf)
        step3.save()
        wf.set_steps({
            0: {'step': step1, 'accept': Actions.go_to_step(1), 'reject': Actions.end_job()},
            1: {'step': step2, 'accept': Actions.go_to_step(2), 'reject': Actions.end_job()},
            2: {'step': step3, 'accept': Actions.end_job()},
        })

        job = Job(workflow=wf)
        job.start()
        self.assertEqual(job.current_step, step1)
        job.accept_step()
        self.assertEqual(job.current_step, step2)
        job.accept_step()
        self.assertEqual(job.current_step, step3)

    def test_workflow_steps_raises_exception_if_job_has_finished(self):
        wf = Workflow()
        wf.save()
        step1 = Step(workflow=wf)
        step2 = Step(workflow=wf)
        step1.save()
        step2.save()
        wf.set_steps({
            0: {'step': step1, 'accept': Actions.go_to_step(1), 'reject': Actions.end_job()},
            1: {'step': step2, 'accept': Actions.end_job()},
        })
        wf.save()
        job = Job(workflow=wf)
        job.start()
        job.accept_step()
        job.accept_step()
        self.assertRaises(JobAlreadyFinishedException, job.accept_step)

    def test_workflow_jobs_remember_step_data(self):
        import json
        wf = Workflow()
        wf.save()
        step1 = Step(workflow=wf)
        step1.save()
        wf.set_steps({
            0: {'step': step1, 'accept': Actions.end_job(), 'reject': Actions.end_job()},
        })
        job = Job(workflow=wf)

        job.start()
        data = {'abc': 123}
        job.set_data_for_step(step=0, data=data)
        data_back = job.get_data_for_step(step=0)

        self.assertEqual(data, data_back)
