"""Base class for pipeline."""

from taskflow.flow import Flow


class PipelineBase(object):
  """Base class of pipeline.

  Subclasses must impolement validate_kwargs and do_build_flow methods.
  """

  def __init__(self, **kwargs):
    self._kwargs = kwargs
    self._flow = self.build_flow(**kwargs)

  def build_flow(self, **kwargs):
    """Make the task flow based on kwargs."""
    self.validate_kwargs(**kwargs)

    # Call do_make_flow implemented by subclass to make the flow.
    flow = self.do_build_flow(**kwargs)
    if not isinstance(flow, Flow):
      raise TypeError('Return type must be taskflow.flow.Flow.')

    # Do some post modification here.

    return flow

  def validate_kwargs(self, **kwargs):
    """Abstract method, subclass must implement this method to validate kwargs."""
    raise NotImplementedError('Subclass must implement abstract method')

  def do_build_flow(self, **kwargs):
    """Abstract method, subclass must implment this method and return a task instance."""
    raise NotImplementedError('Subclass must implement abstract method')

  @property
  def flow(self):
    return self._flow

  @property
  def name(self):
    return self.__class__.__name__

  @property
  def kwargs(self):
    return self._kwargs
