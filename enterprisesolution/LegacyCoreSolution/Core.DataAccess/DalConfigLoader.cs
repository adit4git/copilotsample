using System;
using System.Configuration;
using System.IO;
using System.Xml.Linq;

namespace Core.DataAccess
{
    public static class DalConfigLoader
    {
        public static XDocument LoadDb2Mappings()
        {
            var path = ConfigurationManager.AppSettings["Db2MappingFile"] ?? "Config/DataAccessMappings/db2.xml";
            return XDocument.Load(path);
        }

        public static XDocument LoadOracleMappings()
        {
            var path = ConfigurationManager.AppSettings["OracleMappingFile"] ?? "Config/DataAccessMappings/oracle.xml";
            return XDocument.Load(path);
        }

        public static string LoadSybaseQuery(string key)
        {
            var path = ConfigurationManager.AppSettings["SybaseQueryFile"] ?? "Config/DataAccessMappings/sybase.ini";
            if (!File.Exists(path)) throw new FileNotFoundException(path);
            string currentSection = null;
            foreach (var line in File.ReadAllLines(path))
            {
                var trimmed = line.Trim();
                if (trimmed.StartsWith("[") && trimmed.EndsWith("]"))
                {
                    currentSection = trimmed.Trim('[', ']');
                    continue;
                }
                if (currentSection == "Queries" && trimmed.StartsWith(key + "="))
                {
                    return trimmed.Substring(key.Length + 1);
                }
            }
            throw new InvalidOperationException("Query key not found: " + key);
        }
    }
}
