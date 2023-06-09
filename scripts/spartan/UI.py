import os
import subprocess
from pathlib import Path
import gradio
from scripts.spartan.shared import logger
from scripts.spartan.Worker import State


class UI:
    def __init__(self, script, world):
        self.script = script
        self.world = world

    # handlers
    @staticmethod
    def user_script_btn():
        user_scripts = Path(os.path.abspath(__file__)).parent.parent.joinpath('user')

        for file in user_scripts.iterdir():
            logger.debug(f"found possible script {file.name}")
            if file.is_file() and file.name.startswith('sync'):
                user_script = file

        suffix = user_script.suffix[1:]

        if suffix == 'ps1':
            subprocess.call(['powershell', user_script])
            return True
        else:
            f = open(user_script, 'r')
            first_line = f.readline().strip()
            if first_line.startswith('#!'):
                shebang = first_line[2:]
                subprocess.call([shebang, user_script])
                return True

        return False

    def benchmark_btn(self):
        logger.info("Redoing benchmarks...")
        self.world.benchmark(rebenchmark=True)

    def interrupt_btn(self):
        self.world.interrupt_remotes()

    def refresh_ckpts_btn(self):
        self.world.refresh_checkpoints()

    def status_btn(self):
        worker_status = ''
        workers = self.world.get_workers()

        for worker in workers:
            if worker.master:
                continue

            worker_status += f"{worker.uuid} at {worker.address} is {worker.state.name}\n"

        # TODO replace this with a single check to a state flag that we should make in the world class
        for worker in workers:
            if worker.state == State.WORKING:
                return self.world.__str__(), worker_status

        return 'No active jobs!', worker_status

    # end handlers

    def create_root(self):
        with gradio.Box() as root:
            with gradio.Accordion(label='Distributed', open=False):
                with gradio.Tab('Status') as status_tab:
                    status = gradio.Textbox(elem_id='status', show_label=False)
                    status.placeholder = 'Refresh!'
                    jobs = gradio.Textbox(elem_id='jobs', label='Jobs', show_label=True)
                    jobs.placeholder = 'Refresh!'

                    refresh_status_btn = gradio.Button(value='Refresh')
                    refresh_status_btn.style(size='sm')
                    refresh_status_btn.click(self.status_btn, inputs=[], outputs=[jobs, status])

                    status_tab.select(fn=self.status_btn, inputs=[], outputs=[jobs, status])

                with gradio.Tab('Utils'):
                    refresh_checkpoints_btn = gradio.Button(value='Refresh checkpoints')
                    refresh_checkpoints_btn.style(full_width=False)
                    refresh_checkpoints_btn.click(self.refresh_ckpts_btn, inputs=[], outputs=[])

                    run_usr_btn = gradio.Button(value='Run user script')
                    run_usr_btn.style(full_width=False)
                    run_usr_btn.click(self.user_script_btn, inputs=[], outputs=[])

                    interrupt_all_btn = gradio.Button(value='Interrupt all', variant='stop')
                    interrupt_all_btn.style(full_width=False)
                    interrupt_all_btn.click(self.interrupt_btn, inputs=[], outputs=[])

                    redo_benchmarks_btn = gradio.Button(value='Redo benchmarks', variant='stop')
                    redo_benchmarks_btn.style(full_width=False)
                    redo_benchmarks_btn.click(self.benchmark_btn, inputs=[], outputs=[])

            return root
