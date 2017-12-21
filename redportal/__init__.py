from .redportal import Redportal


def setup(bot):
    bot.add_cog(Redportal(bot))
