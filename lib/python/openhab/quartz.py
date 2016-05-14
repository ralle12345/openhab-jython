"""
Quartz scheduler utilities for manipulating scheduled jobs.
"""
import types

from openhab.globals import oh
from org.openhab.core.jsr223.internal.actions import Timer
from org.quartz.impl.matchers import GroupMatcher

log = oh.getLogger(__name__)

def visit_jobs(scheduler, visitor, group_filter=None, job_filter=None):
    # Transform group filter
    if isinstance(group_filter, types.StringTypes):
        filter_name = group_filter
        group_filter = lambda name: name == filter_name
    elif hasattr(group_filter, "__iter__"):
        group_filter = lambda name: name in group_filter
    # Visit
    if hasattr(visitor, "visit_scheduler"):
        visitor.visit_scheduler(scheduler)
    for group_name in Timer.scheduler.getJobGroupNames():
        if group_filter is None or group_filter(group_name):
            if hasattr(visitor, "visit_group"):
                visitor.visit_group(scheduler, group_name)
            for jobkey in Timer.scheduler.getJobKeys(GroupMatcher.groupEquals(group_name)):
                if job_filter is None or job_filter(jobkey):
                    if hasattr(visitor, "visit_jobkey"):
                        visitor.visit_jobkey(scheduler, group_name, jobkey)
                    if hasattr(visitor, "visit_trigger"):
                        for trigger in Timer.scheduler.getTriggersOfJob(jobkey):
                            visitor.visit_trigger(scheduler, group_name, jobkey, trigger)

class JobPrinter(object):
    def visit_scheduler(self, scheduler):
        log.info("Scheduler: {}".format(scheduler))

    def visit_group(self, scheduler, group_name):
        log.info("  Group: {}".format(group_name))

    def visit_jobkey(self, scheduler, group_name, jobkey):
        detail = scheduler.getJobDetail(jobkey)
        datamap = detail.getJobDataMap()
        if 'rule' in datamap:
            log.info("    Job: {}".format(datamap['rule']))
        else:
            log.info("    Job: {}".format(jobkey.name))

    def visit_trigger(self, scheduler, group_name, jobkey, trigger):
        log.info("      Trigger {}".format(str(trigger.getNextFireTime())))

def log_jobs(job_filter=None, group_filter=lambda group: True):
    visit_jobs(Timer.scheduler, JobPrinter(), group_filter=group_filter, job_filter=job_filter)

def delete_jsr223_jobs(job_filter=None):
    class DeleteJob(object):
        def visit_jobkey(self, scheduler, group_name, jobkey):
            scheduler.deleteJob(jobkey)
            log.info("Quartz job deleted: {}", str(jobkey))
    visit_jobs(Timer.scheduler, DeleteJob(), group_filter="DEFAULT", job_filter=job_filter)

from org.quartz import Job, JobDataMap, JobBuilder, TriggerBuilder, SimpleScheduleBuilder
from org.quartz.impl import StdSchedulerFactory

_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = StdSchedulerFactory.getDefaultScheduler()
    return _scheduler

class QuartzCallbackJob(Job):
    def execute(self, context):
        context.jobDetail.jobDataMap.get("callback")()
        
def schedule_periodic_callback(callback, period_millis):
    job_map = JobDataMap()
    job_map.put("callback", callback)
    job = JobBuilder.newJob(QuartzCallbackJob).usingJobData(job_map).build()
    schedule = SimpleScheduleBuilder.simpleSchedule().repeatForever().withIntervalInMilliseconds(period_millis)
    trigger = TriggerBuilder.newTrigger().startNow().withSchedule(schedule).build()
    get_scheduler().scheduleJob(job, trigger)
    return job.key
